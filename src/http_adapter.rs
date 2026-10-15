use std::{net::SocketAddr, sync::Arc, time::Duration};

use reqwest::{Client, Method, Url};
use rmcp::{
    ErrorData, RoleServer, ServerHandler,
    model::{
        CallToolRequestParams, CallToolResponse, CallToolResult, ContentBlock, ListToolsResult,
        PaginatedRequestParams, ServerCapabilities, ServerConfig, Tool,
    },
    service::RequestContext,
};
use serde_json::{Value, json};

use crate::actions::{Operation, contract};

const MAX_BODY: usize = 1024 * 1024;
pub const TEST_API_KEY: &str = "mock-api-key-not-production";

#[derive(Clone)]
pub struct HttpTestAdapter {
    client: Client,
    base: Url,
    timeout: Duration,
}

impl HttpTestAdapter {
    pub fn new(address: SocketAddr, timeout: Duration) -> Result<Self, &'static str> {
        if !address.ip().is_loopback() || address.port() == 0 || timeout.is_zero() {
            return Err("only_explicit_loopback_test_endpoints_allowed");
        }
        let client = Client::builder()
            .no_proxy()
            .redirect(reqwest::redirect::Policy::none())
            .retry(reqwest::retry::never())
            .timeout(timeout)
            .connect_timeout(timeout)
            .build()
            .map_err(|_| "client_configuration_error")?;
        let base =
            Url::parse(&format!("http://{address}/")).map_err(|_| "invalid_test_endpoint")?;
        Ok(Self {
            client,
            base,
            timeout,
        })
    }

    pub async fn call(&self, name: &str, args: Value) -> Result<CallToolResult, ErrorData> {
        let operation = contract()
            .operations
            .into_iter()
            .find(|operation| operation.name == name)
            .ok_or_else(|| ErrorData::invalid_params("unknown_action", None))?;
        let validator = jsonschema::options()
            .should_validate_formats(true)
            .build(&operation.input)
            .map_err(|_| ErrorData::internal_error("invalid_embedded_schema", None))?;
        if serde_json::to_vec(&args).map_or(true, |bytes| bytes.len() > 16384)
            || !validator.is_valid(&args)
        {
            return Err(ErrorData::invalid_params("invalid_input", None));
        }
        let (mut url, query) = self.route(&operation, &args)?;
        if !query.is_empty() {
            url.query_pairs_mut().extend_pairs(&query);
        }
        let method = Method::from_bytes(operation.method.as_bytes())
            .map_err(|_| ErrorData::internal_error("invalid_method", None))?;
        let mut request = self
            .client
            .request(method, url)
            .header("X-API-Key", TEST_API_KEY)
            .header("Accept", "application/json");
        if let Some(body) = args.get("body") {
            request = request.json(body);
        }
        let outcome = tokio::time::timeout(self.timeout, async {
            let mut response = request.send().await.map_err(|error| {
                if error.is_timeout() {
                    "timeout"
                } else {
                    "transport_unavailable"
                }
            })?;
            let status = response.status().as_u16();
            if !(200..300).contains(&status) {
                return Ok((
                    Some(status),
                    Err(match status {
                        401 => "unauthorized",
                        403 => "forbidden",
                        404 => "not_found",
                        409 => "conflict",
                        400 | 422 => "invalid_request",
                        300..=399 => "redirect_refused",
                        500..=599 => "upstream_unavailable",
                        _ => "http_error",
                    }),
                ));
            }
            if response
                .content_length()
                .is_some_and(|size| size > MAX_BODY as u64)
            {
                return Err("response_too_large");
            }
            let mut bytes = Vec::new();
            while let Some(chunk) = response.chunk().await.map_err(|_| "response_read_failed")? {
                if bytes.len() + chunk.len() > MAX_BODY {
                    return Err("response_too_large");
                }
                bytes.extend_from_slice(&chunk);
            }
            let data: Value =
                serde_json::from_slice(&bytes).map_err(|_| "invalid_json_response")?;
            let schema = operation
                .responses
                .get(&status.to_string())
                .or_else(|| operation.responses.get("default"))
                .ok_or("undocumented_success_status")?;
            let validator = jsonschema::options()
                .should_validate_formats(true)
                .build(schema)
                .map_err(|_| "invalid_response_schema")?;
            if !validator.is_valid(&data) {
                return Err("invalid_response_shape");
            }
            Ok((Some(status), Ok(data)))
        })
        .await;
        let (status, result) = match outcome {
            Ok(Ok(result)) => result,
            Ok(Err(error)) => (None, Err(error)),
            Err(_) => (None, Err("timeout")),
        };
        Ok(response(status, result))
    }

    fn route(
        &self,
        operation: &Operation,
        args: &Value,
    ) -> Result<(Url, Vec<(String, String)>), ErrorData> {
        let mut url = self.base.clone();
        {
            let mut path = url
                .path_segments_mut()
                .map_err(|_| ErrorData::internal_error("invalid_base", None))?;
            path.clear();
            for segment in operation.path.trim_start_matches('/').split('/') {
                if let Some(name) = segment
                    .strip_prefix('{')
                    .and_then(|value| value.strip_suffix('}'))
                {
                    path.push(&scalar(&args[name])?);
                } else {
                    path.push(segment);
                }
            }
        }
        let mut query = Vec::new();
        for (name, value) in args
            .as_object()
            .ok_or_else(|| ErrorData::invalid_params("expected_object", None))?
        {
            if name == "body"
                || operation
                    .parameter_locations
                    .get(name)
                    .is_some_and(|location| location == "path")
            {
                continue;
            }
            let metadata = operation.parameter_metadata.get(name);
            if metadata
                .and_then(|value| value.get("style"))
                .and_then(Value::as_str)
                .is_some_and(|style| style != "form")
            {
                return Err(ErrorData::invalid_params("unsupported_query_style", None));
            }
            if let Some(values) = value.as_array() {
                let values = values.iter().map(scalar).collect::<Result<Vec<_>, _>>()?;
                if metadata
                    .and_then(|value| value.get("explode"))
                    .and_then(Value::as_bool)
                    == Some(false)
                {
                    query.push((name.clone(), values.join(",")));
                } else {
                    query.extend(values.into_iter().map(|value| (name.clone(), value)));
                }
            } else {
                query.push((name.clone(), scalar(value)?));
            }
        }
        Ok((url, query))
    }
}

fn scalar(value: &Value) -> Result<String, ErrorData> {
    match value {
        Value::String(value) => Ok(value.clone()),
        Value::Number(value) => Ok(value.to_string()),
        Value::Bool(value) => Ok(value.to_string()),
        Value::Null => Ok(String::new()),
        _ => Err(ErrorData::invalid_params(
            "unsupported_parameter_serialization",
            None,
        )),
    }
}

fn response(status: Option<u16>, result: Result<Value, &str>) -> CallToolResult {
    let (envelope, failed) = match result {
        Ok(data) => (
            json!({"test_http":true,"http_status":status,"data":data}),
            false,
        ),
        Err(error) => (
            json!({"test_http":true,"http_status":status,"error":error}),
            true,
        ),
    };
    let contents = vec![ContentBlock::text(envelope.to_string())];
    let mut response = if failed {
        CallToolResult::error(contents)
    } else {
        CallToolResult::success(contents)
    };
    response.structured_content = Some(envelope);
    response
}

#[derive(Clone)]
pub struct HttpActionsTestServer {
    adapter: HttpTestAdapter,
    tools: Arc<Vec<Tool>>,
}

impl HttpActionsTestServer {
    pub fn new(adapter: HttpTestAdapter) -> Result<Self, Box<dyn std::error::Error>> {
        let mut tools = Vec::new();
        for operation in contract().operations {
            let read_only = operation.method == "GET";
            let output = json!({"type":"object","properties":{"test_http":{"const":true},"http_status":{"type":["integer","null"]},"data":operation.responses["200"],"error":{"type":"string"}},"required":["test_http","http_status"],"oneOf":[{"required":["data"]},{"required":["error"]}],"additionalProperties":false});
            tools.push(serde_json::from_value(json!({"name":operation.name,"description":format!("HTTP DI COLLAUDO SU LOOPBACK: {} {}. Nessuna API o credenziale reale.",operation.method,operation.path),"inputSchema":operation.input,"outputSchema":output,"annotations":{"readOnlyHint":read_only,"destructiveHint":!read_only,"idempotentHint":read_only,"openWorldHint":false}}))?);
        }
        Ok(Self {
            adapter,
            tools: Arc::new(tools),
        })
    }
}

impl ServerHandler for HttpActionsTestServer {
    fn get_info(&self) -> ServerConfig {
        ServerConfig::new(ServerCapabilities::builder().enable_tools().build())
    }
    fn get_tool(&self, name: &str) -> Option<Tool> {
        self.tools.iter().find(|tool| tool.name == name).cloned()
    }
    async fn list_tools(
        &self,
        _request: Option<PaginatedRequestParams>,
        _context: RequestContext<RoleServer>,
    ) -> Result<ListToolsResult, ErrorData> {
        Ok(ListToolsResult {
            tools: self.tools.as_ref().clone(),
            ..Default::default()
        })
    }
    async fn call_tool(
        &self,
        request: CallToolRequestParams,
        _context: RequestContext<RoleServer>,
    ) -> Result<CallToolResponse, ErrorData> {
        self.adapter
            .call(
                &request.name,
                Value::Object(request.arguments.unwrap_or_default()),
            )
            .await
            .map(Into::into)
    }
}
