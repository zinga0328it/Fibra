use std::{net::SocketAddr, sync::Arc, time::Duration};

use reqwest::header::HeaderValue;
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

#[path = "live_contract.rs"]
mod live_contract;

const MAX_BODY: usize = 1024 * 1024;
const MAX_COLLECTION_BODY: usize = 16 * MAX_BODY;
pub const TEST_API_KEY: &str = "mock-api-key-not-production";

#[derive(Clone)]
pub struct HttpTestAdapter {
    client: Client,
    base: Url,
    timeout: Duration,
    api_key: HeaderValue,
    production: bool,
    writes_enabled: bool,
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
            api_key: HeaderValue::from_static(TEST_API_KEY),
            production: false,
            writes_enabled: true,
        })
    }

    pub async fn call(&self, name: &str, mut args: Value) -> Result<CallToolResult, ErrorData> {
        let mut operation = contract()
            .operations
            .into_iter()
            .find(|operation| operation.name == name)
            .ok_or_else(|| ErrorData::invalid_params("unknown_action", None))?;
        if self.production {
            live_contract::adapt(&mut operation);
            live_contract::prepare_arguments(name, &mut args)
                .map_err(|error| ErrorData::invalid_params(error, None))?;
        }
        let validator = jsonschema::options()
            .with_format("ftth-date-time", live_contract::valid_datetime)
            .should_validate_formats(true)
            .build(&operation.input)
            .map_err(|_| ErrorData::internal_error("invalid_embedded_schema", None))?;
        if serde_json::to_vec(&args).map_or(true, |bytes| bytes.len() > 16384)
            || !validator.is_valid(&args)
        {
            return Err(ErrorData::invalid_params("invalid_input", None));
        }
        if self.production && !self.writes_enabled && operation.method != "GET" {
            return Ok(response(None, Err("live_writes_disabled"), true, false));
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
            .header("X-API-Key", self.api_key.clone())
            .header("Accept", "application/json");
        if let Some(body) = args.get("body") {
            request = request.json(body);
        }
        let body_limit = if self.production
            && matches!(name, "getWorks" | "getModems" | "getONTs" | "getDocuments")
        {
            MAX_COLLECTION_BODY
        } else {
            MAX_BODY
        };
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
                        429 => "rate_limited",
                        400 | 422 => "invalid_request",
                        300..=399 => "redirect_refused",
                        500..=599 => "upstream_unavailable",
                        _ => "http_error",
                    }),
                ));
            }
            if response
                .content_length()
                .is_some_and(|size| size > body_limit as u64)
            {
                return Err("response_too_large");
            }
            let mut bytes = Vec::new();
            while let Some(chunk) = response.chunk().await.map_err(|_| "response_read_failed")? {
                if bytes.len() + chunk.len() > body_limit {
                    return Err("response_too_large");
                }
                bytes.extend_from_slice(&chunk);
            }
            let mut data: Value =
                serde_json::from_slice(&bytes).map_err(|_| "invalid_json_response")?;
            if self.production
                && operation.name == "getHealth"
                && let Some(timestamp) = data.get("timestamp").and_then(Value::as_str)
                && let Ok(timestamp) =
                    chrono::NaiveDateTime::parse_from_str(timestamp, "%Y-%m-%dT%H:%M:%S%.f")
            {
                data["timestamp"] = json!(
                    timestamp
                        .and_utc()
                        .to_rfc3339_opts(chrono::SecondsFormat::AutoSi, true)
                );
            }
            let schema = operation
                .responses
                .get(&status.to_string())
                .or_else(|| operation.responses.get("default"))
                .ok_or("undocumented_success_status")?;
            let validator = jsonschema::options()
                .with_format("ftth-date-time", live_contract::valid_datetime)
                .should_validate_formats(true)
                .build(schema)
                .map_err(|_| "invalid_response_schema")?;
            if !validator.is_valid(&data) {
                return Ok((Some(status), Err("invalid_response_shape")));
            }
            Ok((Some(status), Ok(data)))
        })
        .await;
        let (status, result) = match outcome {
            Ok(Ok(result)) => result,
            Ok(Err(error)) => (None, Err(error)),
            Err(_) => (None, Err("timeout")),
        };
        let result = match result {
            Ok(data)
                if self.production
                    && operation.method != "GET"
                    && data.get("ok") == Some(&Value::Bool(false)) =>
            {
                Err("upstream_operation_failed")
            }
            other => other,
        };
        let failed = result.is_err();
        let mut output = response(status, result, self.production, self.writes_enabled);
        if self.production && operation.method != "GET" {
            let outcome = if !failed {
                "completed"
            } else if status.is_some_and(|status| (400..500).contains(&status)) {
                "rejected"
            } else {
                "unknown"
            };
            let envelope = output.structured_content.as_mut().unwrap();
            envelope["write_outcome"] = json!(outcome);
            output.content = vec![ContentBlock::text(envelope.to_string())];
        }
        Ok(output)
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
            path.pop_if_empty();
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

fn response(
    status: Option<u16>,
    result: Result<Value, &str>,
    production: bool,
    writes_enabled: bool,
) -> CallToolResult {
    let (mut envelope, failed) = match result {
        Ok(data) => (
            json!({"test_http":true,"http_status":status,"data":data}),
            false,
        ),
        Err(error) => (
            json!({"test_http":true,"http_status":status,"error":error}),
            true,
        ),
    };
    if production {
        envelope.as_object_mut().unwrap().remove("test_http");
        envelope["simulated"] = json!(false);
        envelope["mode"] = json!(if writes_enabled {
            "live_read_write"
        } else {
            "live_read_only"
        });
    }
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
pub struct ProductionAdapter {
    adapter: HttpTestAdapter,
}

impl ProductionAdapter {
    pub fn new(api_key: String) -> Result<Self, &'static str> {
        if api_key.trim().is_empty() || api_key == TEST_API_KEY {
            return Err("production_api_key_required");
        }
        let mut api_key = HeaderValue::from_str(&api_key).map_err(|_| "invalid_api_key_format")?;
        api_key.set_sensitive(true);
        let timeout = Duration::from_secs(30);
        let client = Client::builder()
            .no_proxy()
            .redirect(reqwest::redirect::Policy::none())
            .retry(reqwest::retry::never())
            .https_only(true)
            .timeout(timeout)
            .connect_timeout(Duration::from_secs(10))
            .build()
            .map_err(|_| "client_configuration_error")?;
        let base = Url::parse("https://servicess.net/gestionale-gpt/")
            .map_err(|_| "invalid_fixed_endpoint")?;
        Ok(Self {
            adapter: HttpTestAdapter {
                client,
                base,
                timeout,
                api_key,
                production: true,
                writes_enabled: false,
            },
        })
    }

    pub async fn call(&self, name: &str, args: Value) -> Result<CallToolResult, ErrorData> {
        self.adapter.call(name, args).await
    }

    pub fn read_write(api_key: String) -> Result<Self, &'static str> {
        let mut adapter = Self::new(api_key)?;
        adapter.adapter.writes_enabled = true;
        Ok(adapter)
    }
}

#[cfg(test)]
mod production_tests {
    use super::*;

    mod support {
        include!(concat!(env!("CARGO_MANIFEST_DIR"), "/tests/support/mod.rs"));
    }

    fn live_test_arguments(operation: &Operation) -> Value {
        let mut args = support::contract_argument(&operation.input, "");
        for name in operation.parameter_locations.keys() {
            if args.get(name).is_none() {
                args[name] = support::contract_argument(&operation.input["properties"][name], name);
            }
        }
        match operation.name.as_str() {
            "updateWork" => args["body"] = json!({"note":"synthetic note"}),
            "updateONT" | "updateModem" => args["body"] = json!({"location":"synthetic location"}),
            "updateAppointment" => args["note_appuntamento"] = json!("synthetic appointment"),
            _ => {}
        }
        args
    }

    #[tokio::test]
    async fn all_32_live_actions_over_mcp_preserve_http_payloads() {
        use axum::{Json, Router, body::to_bytes, extract::Request};
        use rmcp::{ServiceExt, model::ClientConfig, transport::StreamableHttpClientTransport};
        use std::sync::Mutex;
        let payload = Arc::new(Mutex::new(json!({})));
        let observations = Arc::new(Mutex::new(Vec::<Value>::new()));
        let captured = observations.clone();
        let reply = payload.clone();
        let upstream = Router::new().fallback(move |request: Request| {
            let captured = captured.clone(); let reply = reply.clone();
            async move {
                let (parts, body) = request.into_parts();
                assert_eq!(parts.headers["x-api-key"], "synthetic-api");
                assert!(!parts.headers.contains_key("x-relay-key"));
                assert!(!parts.headers.contains_key("x-internal-key"));
                let bytes = to_bytes(body, 16384).await.unwrap();
                let body = if bytes.is_empty() { Value::Null } else { serde_json::from_slice(&bytes).unwrap() };
                let url = Url::parse(&format!("http://localhost{}", parts.uri)).unwrap();
                let query: std::collections::BTreeMap<_,_> = url.query_pairs().into_owned().collect();
                captured.lock().unwrap().push(json!({"method":parts.method.as_str(),"path":parts.uri.path(),"query":query,"body":body}));
                Json(reply.lock().unwrap().clone())
            }
        });
        let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
        let address = listener.local_addr().unwrap();
        let upstream_task = tokio::spawn(async move {
            axum::serve(listener, upstream).await.unwrap();
        });
        let mut adapter = ProductionAdapter::read_write("synthetic-api".into()).unwrap();
        adapter.adapter.client = HttpTestAdapter::new(address, Duration::from_secs(3))
            .unwrap()
            .client;
        adapter.adapter.base = Url::parse(&format!("http://{address}/gestionale-gpt/")).unwrap();
        let router = live_http_router(LiveActionsServer::new(adapter).unwrap());
        let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
        let address = listener.local_addr().unwrap();
        let mcp_task = tokio::spawn(async move {
            axum::serve(listener, router).await.unwrap();
        });
        let outcome = tokio::time::timeout(Duration::from_secs(30), async {
            let client = ClientConfig::default()
                .serve(StreamableHttpClientTransport::from_uri(format!(
                    "http://{address}/mcp"
                )))
                .await
                .unwrap();
            let tools = client.list_all_tools().await.unwrap();
            assert_eq!(tools.len(), 38);
            for (index, operation) in contract().operations.into_iter().enumerate() {
                let args = live_test_arguments(&operation);
                let expected = if operation.name == "getYearlyStats" {
                    json!([{"date":"2026-10","closed":1}])
                } else {
                    crate::actions::ActionsServer::new()
                        .unwrap()
                        .invoke(&operation.name, args.clone())
                        .unwrap()
                        .structured_content
                        .unwrap()["data"]
                        .clone()
                };
                *payload.lock().unwrap() = expected.clone();
                let result = client
                    .call_tool(
                        serde_json::from_value(json!({"name":operation.name,"arguments":args}))
                            .unwrap(),
                    )
                    .await
                    .unwrap();
                assert_ne!(
                    result.is_error,
                    Some(true),
                    "{}: {:?}",
                    operation.name,
                    result.structured_content
                );
                let envelope = result.structured_content.unwrap();
                assert_eq!(envelope["simulated"], false);
                assert_eq!(envelope["mode"], "live_read_write");
                assert_eq!(envelope["data"], expected);
                if operation.method != "GET" {
                    assert_eq!(envelope["write_outcome"], "completed");
                }
                let metadata = serde_json::to_value(
                    tools
                        .iter()
                        .find(|tool| tool.name == operation.name)
                        .unwrap(),
                )
                .unwrap();
                assert!(
                    jsonschema::is_valid(&metadata["outputSchema"], &envelope),
                    "{}",
                    operation.name
                );
                assert_eq!(
                    metadata["annotations"]["readOnlyHint"],
                    operation.method == "GET"
                );
                let observations = observations.lock().unwrap();
                assert_eq!(observations.len(), index + 1);
                let observed = observations.last().unwrap();
                assert_eq!(observed["method"], operation.method);
                let mut path = format!("/gestionale-gpt{}", operation.path);
                let mut query = json!({});
                for (name, location) in &operation.parameter_locations {
                    let value = scalar(&args[name]).unwrap();
                    if location == "path" {
                        path = path.replace(&format!("{{{name}}}"), &value);
                    } else {
                        query[name] = json!(value);
                    }
                }
                assert_eq!(observed["path"], path);
                assert_eq!(observed["query"], query);
                assert_eq!(observed["body"], args["body"]);
            }
            client.cancel().await.unwrap();
        })
        .await;
        mcp_task.abort();
        upstream_task.abort();
        outcome.expect("all live actions protocol timeout");
    }

    #[test]
    fn production_route_preserves_prefix_and_sensitive_key() {
        let adapter = ProductionAdapter::new("synthetic-test-value".into()).unwrap();
        let operation = contract()
            .operations
            .into_iter()
            .find(|operation| operation.name == "getWorkById")
            .unwrap();
        let (url, _query) = adapter
            .adapter
            .route(&operation, &json!({"work_id":7}))
            .unwrap();
        assert_eq!(url.as_str(), "https://servicess.net/gestionale-gpt/works/7");
        assert!(adapter.adapter.api_key.is_sensitive());
        assert!(ProductionAdapter::new(TEST_API_KEY.into()).is_err());
        assert!(ProductionAdapter::new(String::new()).is_err());
        assert!(ProductionAdapter::new("invalid\nheader".into()).is_err());
    }

    #[tokio::test]
    async fn live_helpers_preserve_wr_identity_and_material_namespaces() {
        use axum::{Json, Router, extract::Request, http::StatusCode};
        use std::sync::{
            Mutex,
            atomic::{AtomicBool, Ordering},
        };
        let works = Arc::new(Mutex::new(vec![
            json!({"id":7,"numero_wr":"000123","nome_cliente":"Synthetic customer","stato":"assegnato","extra_fields":null,"data_apertura":"2026-10-16T08:00:00"}),
            json!({"id":123,"numero_wr":"123","stato":"chiuso"}),
        ]));
        let deny_inventory = Arc::new(AtomicBool::new(false));
        let stored_works = works.clone();
        let deny = deny_inventory.clone();
        let router = Router::new().fallback(move |request: Request| {
            let works = stored_works.clone(); let deny = deny.clone();
            async move {
                assert_eq!(request.method(), "GET");
                if deny.load(Ordering::SeqCst) && request.uri().path().contains("/onts/") {
                    return (StatusCode::FORBIDDEN, Json(json!({"detail":"synthetic-private-error"})));
                }
                let ont = json!({"id":1,"serial_number":"ONT-SYNTHETIC","model":"Synthetic ONT","status":"available","manufacturer":null,"location":null,"created_at":"2026-10-16T08:00:00"});
                let modem = json!({"id":1,"serial_number":"MODEM-SYNTHETIC","model":"Synthetic Modem","status":"assigned","type":"fiber","wifi_password":"synthetic-private-wifi","admin_password":"synthetic-private-admin","updated_at":"2026-10-16T08:00:00"});
                let value = match request.uri().path() {
                    "/gestionale-gpt/works/" => json!(works.lock().unwrap().clone()),
                    "/gestionale-gpt/works/7" => works.lock().unwrap()[0].clone(),
                    "/gestionale-gpt/onts/" => json!([ont]),
                    "/gestionale-gpt/modems/" => json!([modem]),
                    "/gestionale-gpt/onts/1" => ont,
                    "/gestionale-gpt/modems/1" => modem,
                    "/gestionale-gpt/health/" => json!({"status":"ok"}),
                    _ => return (StatusCode::NOT_FOUND, Json(json!({"detail":"not_found"}))),
                };
                (StatusCode::OK, Json(value))
            }
        });
        let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
        let address = listener.local_addr().unwrap();
        let server = tokio::spawn(async move {
            axum::serve(listener, router).await.unwrap();
        });
        let mut adapter = ProductionAdapter::read_write("synthetic-api".into()).unwrap();
        adapter.adapter.client = HttpTestAdapter::new(address, Duration::from_secs(3))
            .unwrap()
            .client;
        adapter.adapter.base = Url::parse(&format!("http://{address}/gestionale-gpt/")).unwrap();
        let live = LiveActionsServer::new(adapter).unwrap();
        for (name, args, field, expected) in [
            (
                "cerca_wr",
                json!({"numero_wr":"000123"}),
                "work_id",
                json!(7),
            ),
            (
                "cerca_wr",
                json!({"numero_wr":"123"}),
                "work_id",
                json!(123),
            ),
            (
                "stato_wr",
                json!({"numero_wr":"000123"}),
                "stato",
                json!("assegnato"),
            ),
            ("riepilogo_wr", json!({}), "totale", json!(2)),
            ("stato_api", json!({}), "status", json!("ok")),
            (
                "fetch",
                json!({"document_id":"work_7"}),
                "numero_wr",
                json!("000123"),
            ),
            (
                "fetch",
                json!({"document_id":"ont_1"}),
                "id",
                json!("ont_1"),
            ),
            (
                "fetch",
                json!({"document_id":"modem_1"}),
                "id",
                json!("modem_1"),
            ),
        ] {
            let result = live.invoke(name, args).await.unwrap();
            assert_ne!(result.is_error, Some(true), "{name}");
            let envelope = result.structured_content.unwrap();
            assert_eq!(envelope["mode"], "live_read_write");
            assert_eq!(envelope["data"][field], expected);
        }
        let found = live
            .invoke("search", json!({"query":"synthetic","limit":20}))
            .await
            .unwrap()
            .structured_content
            .unwrap();
        let ids: Vec<_> = found["data"]["results"]
            .as_array()
            .unwrap()
            .iter()
            .map(|item| item["id"].as_str().unwrap())
            .collect();
        assert_eq!(ids, ["work_7", "ont_1", "modem_1"]);
        assert!(!found.to_string().contains("synthetic-private"));
        let limited = live
            .invoke("search", json!({"query":"synthetic","limit":1}))
            .await
            .unwrap()
            .structured_content
            .unwrap();
        assert_eq!(limited["data"]["results"].as_array().unwrap().len(), 1);
        let absent = live
            .invoke("cerca_wr", json!({"numero_wr":"7"}))
            .await
            .unwrap();
        assert_eq!(absent.structured_content.unwrap()["error"], "not_found");
        works
            .lock()
            .unwrap()
            .push(json!({"id":8,"numero_wr":"000123","stato":"aperto"}));
        for name in ["cerca_wr", "stato_wr"] {
            let result = live
                .invoke(name, json!({"numero_wr":"000123"}))
                .await
                .unwrap();
            assert_eq!(result.structured_content.unwrap()["error"], "ambiguous");
        }
        deny_inventory.store(true, Ordering::SeqCst);
        let failed = live
            .invoke("search", json!({"query":"synthetic"}))
            .await
            .unwrap();
        assert_eq!(failed.is_error, Some(true));
        let envelope = failed.structured_content.unwrap();
        assert_eq!(envelope["error"], "forbidden");
        assert!(envelope.get("data").is_none());
        assert!(!envelope.to_string().contains("synthetic-private"));
        server.abort();
    }

    #[tokio::test]
    async fn all_live_writes_never_retry_errors_or_timeouts() {
        use axum::{Router, body::Body, response::Response};
        use std::sync::{
            Mutex,
            atomic::{AtomicUsize, Ordering},
        };
        let state = Arc::new(Mutex::new((200_u16, false)));
        let requests = Arc::new(AtomicUsize::new(0));
        let config = state.clone();
        let observed = requests.clone();
        let router = Router::new().fallback(move || {
            let config = config.clone();
            let observed = observed.clone();
            async move {
                observed.fetch_add(1, Ordering::SeqCst);
                let (status, delay) = *config.lock().unwrap();
                if delay {
                    tokio::time::sleep(Duration::from_millis(400)).await;
                }
                Response::builder()
                    .status(status)
                    .header("Location", "http://192.0.2.1/never-follow")
                    .body(Body::from("synthetic-private-error"))
                    .unwrap()
            }
        });
        let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
        let address = listener.local_addr().unwrap();
        let server = tokio::spawn(async move {
            axum::serve(listener, router).await.unwrap();
        });
        let mut adapter = ProductionAdapter::read_write("synthetic-api".into()).unwrap();
        adapter.adapter.timeout = Duration::from_millis(150);
        adapter.adapter.client = HttpTestAdapter::new(address, Duration::from_millis(150))
            .unwrap()
            .client;
        adapter.adapter.base = Url::parse(&format!("http://{address}/gestionale-gpt/")).unwrap();
        let writes: Vec<_> = contract()
            .operations
            .into_iter()
            .filter(|operation| operation.method != "GET")
            .collect();
        assert_eq!(writes.len(), 15);
        let mut expected_count = 0;
        for operation in writes {
            for (status, delay, expected) in [
                (401, false, "unauthorized"),
                (403, false, "forbidden"),
                (404, false, "not_found"),
                (409, false, "conflict"),
                (422, false, "invalid_request"),
                (429, false, "rate_limited"),
                (503, false, "upstream_unavailable"),
                (302, false, "redirect_refused"),
                (200, true, "timeout"),
            ] {
                *state.lock().unwrap() = (status, delay);
                let result = adapter
                    .call(&operation.name, live_test_arguments(&operation))
                    .await
                    .unwrap();
                assert_eq!(result.is_error, Some(true));
                let envelope = result.structured_content.unwrap();
                assert_eq!(envelope["error"], expected, "{}", operation.name);
                assert_eq!(
                    envelope["write_outcome"],
                    if (400..500).contains(&status) {
                        "rejected"
                    } else {
                        "unknown"
                    }
                );
                assert!(!envelope.to_string().contains("synthetic-private"));
                expected_count += 1;
                assert_eq!(
                    requests.load(Ordering::SeqCst),
                    expected_count,
                    "{} retried",
                    operation.name
                );
            }
        }
        server.abort();
    }

    #[tokio::test]
    async fn production_request_preserves_prefix_without_internal_credentials() {
        use axum::{Json, Router, extract::Request, routing::get};
        let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
        let address = listener.local_addr().unwrap();
        let app = Router::new()
            .route(
                "/gestionale-gpt/health/",
                get(|request: Request| async move {
                    assert_eq!(request.headers()["x-api-key"], "synthetic-api");
                    assert!(!request.headers().contains_key("x-relay-key"));
                    assert!(!request.headers().contains_key("x-internal-key"));
                    Json(json!({"status":"ok","timestamp":"2026-10-15T12:34:56.123456"}))
                }),
            )
            .route(
                "/gestionale-gpt/works/7",
                get(|| async { Json(json!({"id":7,"numero_wr":"000123","stato":"aperto"})) }),
            );
        let server = tokio::spawn(async move {
            axum::serve(listener, app).await.unwrap();
        });
        let mut adapter = ProductionAdapter::new("synthetic-api".into()).unwrap();
        assert_eq!(
            adapter.adapter.base.as_str(),
            "https://servicess.net/gestionale-gpt/"
        );
        adapter.adapter.client = HttpTestAdapter::new(address, Duration::from_secs(3))
            .unwrap()
            .client;
        adapter.adapter.base = Url::parse(&format!("http://{address}/gestionale-gpt/")).unwrap();
        let live = LiveActionsServer::new(adapter).unwrap();
        let result = live.invoke("stato_api", json!({})).await.unwrap();
        let fetched = live
            .invoke("fetch", json!({"document_id":"work_7"}))
            .await
            .unwrap();
        assert_ne!(fetched.is_error, Some(true));
        let fetched = fetched.structured_content.unwrap();
        assert_eq!(fetched["simulated"], false);
        assert_eq!(fetched["data"]["id"], "work_7");
        assert_eq!(fetched["data"]["type"], "work");
        assert_eq!(fetched["data"]["numero_wr"], "000123");
        server.abort();
        let _shutdown = server.await;
        assert_ne!(result.is_error, Some(true));
        let result = result.structured_content.unwrap();
        assert_eq!(result["simulated"], false);
        assert_eq!(result["data"]["status"], "ok");
        assert_eq!(result["data"]["timestamp"], "2026-10-15T12:34:56.123456Z");
        assert!(!result.to_string().contains("synthetic-api"));
    }

    #[tokio::test]
    async fn live_health_normalizes_only_verified_legacy_utc_timestamp() {
        use axum::{Json, Router, extract::State};
        use std::sync::Mutex;
        let payload = Arc::new(Mutex::new(json!({})));
        let router = Router::new()
            .fallback(|State(payload): State<Arc<Mutex<Value>>>| async move {
                Json(payload.lock().unwrap().clone())
            })
            .with_state(payload.clone());
        let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
        let address = listener.local_addr().unwrap();
        let server = tokio::spawn(async move {
            axum::serve(listener, router).await.unwrap();
        });
        let mut adapter = ProductionAdapter::new("synthetic-api".into()).unwrap();
        adapter.adapter.client = HttpTestAdapter::new(address, Duration::from_secs(3))
            .unwrap()
            .client;
        adapter.adapter.base = Url::parse(&format!("http://{address}/gestionale-gpt/")).unwrap();
        for (name, body, failed) in [
            (
                "getHealth",
                json!({"status":"ok","timestamp":"2026-10-15T12:34:56"}),
                false,
            ),
            (
                "getHealth",
                json!({"status":"ok","timestamp":"2026-10-15T12:34:56+02:00"}),
                false,
            ),
            (
                "getHealth",
                json!({"status":"ok","timestamp":"2026-10-15T12:34:56Z"}),
                false,
            ),
            (
                "getHealth",
                json!({"status":"ok","timestamp":"2026-02-30T12:34:56"}),
                true,
            ),
            ("getHealth", json!({"status":"ok","timestamp":123}), true),
            (
                "getHealth",
                json!({"status":true,"timestamp":"2026-10-15T12:34:56"}),
                true,
            ),
            (
                "getWorkById",
                json!({"id":7,"data_apertura":"2026-10-15T12:34:56"}),
                false,
            ),
            (
                "getWorkById",
                json!({"id":7,"data_apertura":"2026-02-30T12:34:56"}),
                true,
            ),
            (
                "getWorkById",
                json!({"id":7,"stato":"assegnato","nome_cliente":null,"extra_fields":null,"data_apertura":null}),
                false,
            ),
        ] {
            *payload.lock().unwrap() = body.clone();
            let args = if name == "getWorkById" {
                json!({"work_id":7})
            } else {
                json!({})
            };
            let result = adapter.call(name, args).await.unwrap();
            assert_eq!(result.is_error.unwrap_or(false), failed);
            let envelope = result.structured_content.unwrap();
            assert_eq!(envelope["http_status"], 200);
            if failed {
                assert_eq!(envelope["error"], "invalid_response_shape");
            } else if body["timestamp"] == "2026-10-15T12:34:56" {
                assert_eq!(envelope["data"]["timestamp"], "2026-10-15T12:34:56Z");
            } else {
                assert_eq!(envelope["data"], body);
            }
        }
        server.abort();
        let _shutdown = server.await;
    }

    #[tokio::test]
    async fn authorized_live_write_reaches_api_once() {
        use axum::{Json, Router, extract::Request};
        use std::sync::atomic::{AtomicUsize, Ordering};
        let requests = Arc::new(AtomicUsize::new(0));
        let captured = requests.clone();
        let operation = contract()
            .operations
            .into_iter()
            .find(|operation| operation.name == "notifyWorkAssignment")
            .unwrap();
        let expected_path = format!(
            "/gestionale-gpt{}",
            operation.path.replace("{work_id}", "7")
        );
        let reply = crate::actions::ActionsServer::new()
            .unwrap()
            .invoke("notifyWorkAssignment", json!({"work_id":7}))
            .unwrap()
            .structured_content
            .unwrap()["data"]
            .clone();
        let router = Router::new().fallback(move |request: Request| {
            let requests = captured.clone();
            let expected_path = expected_path.clone();
            let reply = reply.clone();
            async move {
                requests.fetch_add(1, Ordering::SeqCst);
                assert_eq!(request.method(), "POST");
                assert_eq!(request.uri().path(), expected_path);
                assert_eq!(request.headers()["x-api-key"], "synthetic-api");
                assert!(!request.headers().contains_key("x-internal-key"));
                assert!(!request.headers().contains_key("x-relay-key"));
                Json(reply)
            }
        });
        let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
        let address = listener.local_addr().unwrap();
        let server = tokio::spawn(async move {
            axum::serve(listener, router).await.unwrap();
        });
        let mut adapter = ProductionAdapter::read_write("synthetic-api".into()).unwrap();
        adapter.adapter.client = HttpTestAdapter::new(address, Duration::from_secs(3))
            .unwrap()
            .client;
        adapter.adapter.base = Url::parse(&format!("http://{address}/gestionale-gpt/")).unwrap();
        let live = LiveActionsServer::new(adapter).unwrap();
        let result = live
            .invoke("notifyWorkAssignment", json!({"work_id":7}))
            .await
            .unwrap();
        assert_ne!(result.is_error, Some(true));
        let envelope = result.structured_content.unwrap();
        assert_eq!(envelope["simulated"], false);
        assert_eq!(envelope["mode"], "live_read_write");
        let tool = live
            .tools
            .iter()
            .find(|tool| tool.name == "notifyWorkAssignment")
            .unwrap();
        assert!(jsonschema::is_valid(
            &Value::Object(tool.output_schema.as_ref().unwrap().as_ref().clone()),
            &envelope
        ));
        assert_eq!(requests.load(Ordering::SeqCst), 1);
        server.abort();
        let _shutdown = server.await;
    }

    #[tokio::test]
    async fn live_payload_translation_and_uncertain_writes() {
        use axum::{
            Router,
            body::{Body, to_bytes},
            extract::Request,
            response::Response,
        };
        use std::sync::Mutex;
        let observed = Arc::new(Mutex::new(Vec::<Value>::new()));
        let captured = observed.clone();
        let router = Router::new().fallback(move |request: Request| {
            let captured = captured.clone();
            async move {
                let body: Value = serde_json::from_slice(&to_bytes(request.into_body(), 16384).await.unwrap()).unwrap();
                captured.lock().unwrap().push(body.clone());
                let reply = if body.get("note") == Some(&json!("bad-response")) { "not-json".into() } else { json!({"id":7,"numero_wr":"000123","stato":"assegnato","data_apertura":"2026-10-16T08:00:00","extra_fields":null}).to_string() };
                Response::builder().status(200).body(Body::from(reply)).unwrap()
            }
        });
        let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
        let address = listener.local_addr().unwrap();
        let server = tokio::spawn(async move {
            axum::serve(listener, router).await.unwrap();
        });
        let mut adapter = ProductionAdapter::read_write("synthetic-api".into()).unwrap();
        adapter.adapter.client = HttpTestAdapter::new(address, Duration::from_secs(3))
            .unwrap()
            .client;
        adapter.adapter.base = Url::parse(&format!("http://{address}/gestionale-gpt/")).unwrap();
        for (body, outcome) in [
            (json!({"tecnico_assegnato":2,"note":null}), "completed"),
            (json!({"note":"bad-response"}), "unknown"),
            (
                json!({"extra_fields":{"custom":null},"telefono_cliente":"000000","modem_sn":"SYNTHETIC-SERIAL","note_chiusura":"Synthetic closure"}),
                "completed",
            ),
        ] {
            let result = adapter
                .call("updateWork", json!({"work_id":7,"body":body}))
                .await
                .unwrap();
            assert_eq!(result.structured_content.unwrap()["write_outcome"], outcome);
        }
        for body in [
            json!({"tecnico_assegnato":2,"tecnico_assegnato_id":3}),
            json!({"extra_fields":["not-an-object"]}),
            json!({"telefono_cliente":123}),
            json!({"modem_sn":123}),
        ] {
            assert!(
                adapter
                    .call("updateWork", json!({"work_id":7,"body":body}))
                    .await
                    .is_err()
            );
        }
        let manual_body = json!({"numero_wr":"000123","operatore":"Synthetic","indirizzo":"Synthetic","note":"Manual note","tecnico_assegnato":2,"extra_fields":{"stato":"metadata-only","custom":null}});
        let result = adapter
            .call("createManualWork", json!({"body":manual_body}))
            .await
            .unwrap();
        assert_ne!(result.is_error, Some(true));
        let requests = observed.lock().unwrap();
        assert_eq!(requests.len(), 4);
        assert_eq!(requests[0], json!({"tecnico_assegnato_id":2,"note":null}));
        assert_eq!(requests[2]["extra_fields"], json!({"custom":null}));
        assert_eq!(requests[2]["modem_sn"], "SYNTHETIC-SERIAL");
        assert_eq!(requests[2]["telefono_cliente"], "000000");
        assert_eq!(requests[2]["note_chiusura"], "Synthetic closure");
        assert_eq!(requests[3]["extra_fields"], manual_body["extra_fields"]);
        assert_eq!(requests[3]["tecnico_assegnato_id"], 2);
        assert!(requests[3].get("stato").is_none());
        server.abort();
    }

    #[tokio::test]
    async fn real_writes_are_rejected_before_network() {
        let adapter = ProductionAdapter::new("synthetic-test-value".into()).unwrap();
        let result = adapter
            .call("notifyWorkAssignment", json!({"work_id":7}))
            .await
            .unwrap();
        assert_eq!(result.is_error, Some(true));
        let result = result.structured_content.unwrap();
        assert_eq!(result["error"], "live_writes_disabled");
        assert_eq!(result["simulated"], false);
        assert_eq!(result["mode"], "live_read_only");
        assert!(result.get("test_http").is_none());
    }

    #[tokio::test]
    async fn live_catalog_and_invalid_inputs_never_fall_back_to_mock() {
        let live =
            LiveActionsServer::new(ProductionAdapter::new("synthetic-test-value".into()).unwrap())
                .unwrap();
        let expected: std::collections::BTreeSet<_> = contract()
            .operations
            .into_iter()
            .chain(crate::actions::helper_operations())
            .map(|operation| operation.name)
            .collect();
        let actual: std::collections::BTreeSet<_> = live
            .tools
            .iter()
            .map(|tool| tool.name.to_string())
            .collect();
        assert_eq!(actual, expected);
        assert_eq!(live.tools.len(), 38);
        for tool in live.tools.iter() {
            let output = tool.output_schema.as_ref().unwrap();
            assert_eq!(output["properties"]["simulated"]["const"], false);
        }
        let material = live
            .invoke("fetch", json!({"document_id":"material_3"}))
            .await
            .unwrap();
        assert_eq!(
            material.structured_content.unwrap()["error"],
            "ambiguous_material_identifier_use_ont_ID_or_modem_ID"
        );
        let blocked = live
            .invoke("notifyWorkAssignment", json!({"work_id":7}))
            .await
            .unwrap();
        assert_eq!(
            blocked.structured_content.unwrap()["error"],
            "live_writes_disabled"
        );
        for (name, args) in [
            ("stato_api", json!({"unexpected":true})),
            ("fetch", json!({"document_id":"work_0"})),
            (
                "fetch",
                json!({"document_id":"work_999999999999999999999999999999999999"}),
            ),
            ("cerca_wr", json!({"numero_wr":123})),
            ("search", json!({"query":"   "})),
            ("fetch", json!({"document_id":"ont_0"})),
            ("unknown", json!({})),
        ] {
            assert!(live.invoke(name, args).await.is_err());
        }
    }

    #[tokio::test]
    async fn live_profile_over_streamable_http() {
        use axum::{
            Json, Router,
            extract::{Path, Request},
            http::StatusCode,
            middleware,
            routing::get,
        };
        use rmcp::{ServiceExt, model::ClientConfig, transport::StreamableHttpClientTransport};
        use std::sync::atomic::{AtomicUsize, Ordering};

        let requests = Arc::new(AtomicUsize::new(0));
        let captured = requests.clone();
        let upstream = Router::new()
            .route(
                "/gestionale-gpt/works/",
                get(|| async { Json(json!([{"id":7,"numero_wr":"000123","stato":"aperto"}])) }),
            )
            .route("/gestionale-gpt/onts/", get(|| async { Json(json!([])) }))
            .route("/gestionale-gpt/modems/", get(|| async { Json(json!([])) }))
            .route(
                "/gestionale-gpt/health/",
                get(|| async { Json(json!({"status":"ok"})) }),
            )
            .route(
                "/gestionale-gpt/works/{work_id}",
                get(|Path(work_id): Path<i64>| async move {
                    match work_id {
                        7 => (
                            StatusCode::OK,
                            Json(json!({"id":7,"numero_wr":"000123","stato":"aperto"})),
                        ),
                        8 => (
                            StatusCode::FORBIDDEN,
                            Json(json!({"detail":"synthetic-upstream-secret"})),
                        ),
                        _ => (StatusCode::OK, Json(json!({"id":999}))),
                    }
                }),
            )
            .layer(middleware::from_fn(
                move |request: Request, next: middleware::Next| {
                    let captured = captured.clone();
                    async move {
                        captured.fetch_add(1, Ordering::SeqCst);
                        assert_eq!(request.headers()["x-api-key"], "synthetic-api");
                        assert!(!request.headers().contains_key("x-relay-key"));
                        assert!(!request.headers().contains_key("x-internal-key"));
                        next.run(request).await
                    }
                },
            ));
        let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
        let address = listener.local_addr().unwrap();
        let upstream_task = tokio::spawn(async move {
            axum::serve(listener, upstream).await.unwrap();
        });
        let mut adapter = ProductionAdapter::new("synthetic-api".into()).unwrap();
        adapter.adapter.client = HttpTestAdapter::new(address, Duration::from_secs(3))
            .unwrap()
            .client;
        adapter.adapter.base = Url::parse(&format!("http://{address}/gestionale-gpt/")).unwrap();
        let router = live_http_router(LiveActionsServer::new(adapter).unwrap());
        let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
        let address = listener.local_addr().unwrap();
        let mcp_task = tokio::spawn(async move {
            axum::serve(listener, router).await.unwrap();
        });
        let outcome = tokio::time::timeout(Duration::from_secs(10), async {
            let client = ClientConfig::default()
                .serve(StreamableHttpClientTransport::from_uri(format!(
                    "http://{address}/mcp"
                )))
                .await
                .unwrap();
            let tools = client.list_all_tools().await.unwrap();
            assert_eq!(tools.len(), 38);
            for (name, args, expected_error) in [
                ("getHealth", json!({}), None),
                ("stato_api", json!({}), None),
                ("fetch", json!({"document_id":"work_7"}), None),
                ("fetch", json!({"document_id":"work_8"}), Some("forbidden")),
                (
                    "fetch",
                    json!({"document_id":"work_9"}),
                    Some("invalid_response_shape"),
                ),
                (
                    "notifyWorkAssignment",
                    json!({"work_id":7}),
                    Some("live_writes_disabled"),
                ),
                ("search", json!({"query":"000123"}), None),
            ] {
                let request =
                    serde_json::from_value(json!({"name":name,"arguments":args})).unwrap();
                let result = client.call_tool(request).await.unwrap();
                assert_eq!(result.is_error.unwrap_or(false), expected_error.is_some());
                let envelope = result.structured_content.unwrap();
                let tool = tools.iter().find(|tool| tool.name == name).unwrap();
                let metadata = serde_json::to_value(tool).unwrap();
                assert!(jsonschema::is_valid(&metadata["outputSchema"], &envelope));
                assert_eq!(envelope["simulated"], false);
                assert_eq!(envelope["mode"], "live_read_only");
                if let Some(error) = expected_error {
                    assert_eq!(envelope["error"], error);
                }
                assert!(!envelope.to_string().contains("synthetic-upstream-secret"));
                assert!(!envelope.to_string().contains("synthetic-api"));
            }
            client.cancel().await.unwrap();
        })
        .await;
        mcp_task.abort();
        upstream_task.abort();
        let _shutdown = mcp_task.await;
        let _shutdown = upstream_task.await;
        outcome.expect("live MCP protocol timeout");
        assert_eq!(requests.load(Ordering::SeqCst), 8);
    }
}

#[derive(Clone)]
pub struct HttpActionsTestServer {
    adapter: HttpTestAdapter,
    tools: Arc<Vec<Tool>>,
}

#[derive(Clone)]
pub struct LiveActionsServer {
    adapter: ProductionAdapter,
    tools: Arc<Vec<Tool>>,
}

fn live_helpers() -> Vec<Operation> {
    let mut helpers = crate::actions::helper_operations();
    for helper in &mut helpers {
        if helper.name == "fetch" {
            helper.input["properties"]["document_id"]["pattern"] =
                json!("^(work|ont|modem|material)_[0-9]+$");
        }
    }
    helpers
}

fn document(record: &Value, kind: &str, compact: bool) -> Option<Value> {
    let api_id = record.get("id")?.as_i64().filter(|api_id| *api_id > 0)?;
    let mut result = if compact {
        let mut selected = json!({});
        for field in [
            "numero_wr",
            "stato",
            "nome_cliente",
            "indirizzo",
            "tipo_lavoro",
            "archived",
            "serial_number",
            "model",
            "manufacturer",
            "location",
            "status",
        ] {
            if let Some(value) = record.get(field) {
                selected[field] = value.clone();
            }
        }
        selected
    } else {
        record.clone()
    };
    if kind == "modem"
        && let Some(modem_type) = record.get("type")
    {
        result["modem_type"] = modem_type.clone();
    }
    result["id"] = json!(format!("{kind}_{api_id}"));
    result["api_id"] = json!(api_id);
    result["type"] = json!(if kind == "work" { "work" } else { "material" });
    if kind == "work" {
        result["work_id"] = json!(api_id);
    } else {
        result["equipment_kind"] = json!(kind);
    }
    Some(result)
}

impl LiveActionsServer {
    pub fn new(adapter: ProductionAdapter) -> Result<Self, Box<dyn std::error::Error>> {
        let mut tools = Vec::new();
        let writes_enabled = adapter.adapter.writes_enabled;
        let mode = if writes_enabled {
            "live_read_write"
        } else {
            "live_read_only"
        };
        for mut operation in contract().operations.into_iter().chain(live_helpers()) {
            live_contract::adapt(&mut operation);
            let read_only = operation.method == "GET";
            let description = match operation.name.as_str() {
                "stato_api" => "GET reale /health/ attraverso l'ingresso configurato. Il risultato non verifica separatamente ciascun nodo.".to_owned(),
                "fetch" => "API REALE: legge work_ID, ont_ID o modem_ID restituiti da search. API ID interno, mai numero WR; material_ID senza tipo e' ambiguo.".to_owned(),
                "search" => "API REALE: consulta gli elenchi lavori, ONT e modem e filtra per WR, cliente, indirizzo, seriale o modello. Restituisce al massimo limit risultati, senza credenziali degli apparati. Nessuna ricerca server-side o paginazione disponibile; letture limitate a 16 MiB ciascuna.".to_owned(),
                "cerca_wr" | "stato_wr" => "API REALE: legge GET /works/ (massimo 16 MiB), cerca numero_wr come stringa esatta conservando gli zeri iniziali. Duplicati producono ambiguous, mai una scelta arbitraria. work_id e' l'ID interno da usare nelle Actions.".to_owned(),
                "riepilogo_wr" => "API REALE: legge GET /works/ (massimo 16 MiB) e conta tutti i lavori, inclusi quelli archiviati, raggruppati per stato.".to_owned(),
                _ if read_only => format!("API REALE in sola lettura: GET {} tramite l'ingresso HTTPS servicess.net/gestionale-gpt e il broker ZINGA. Nessun dato simulato.", operation.path),
                _ if writes_enabled => format!("API REALE: {} {}. Modifica dati o invia notifiche nel gestionale. Usare solo per richieste esplicite dell'utente; nessun ritentativo automatico.", operation.method, operation.path),
                _ => "Action conservata ma BLOCCATA nel profilo reale di sola lettura: live_writes_disabled.".to_owned(),
            };
            let output = json!({"type":"object","properties":{"simulated":{"const":false},"mode":{"const":mode},"http_status":{"type":["integer","null"]},"data":operation.responses["200"],"error":{"type":"string"},"write_outcome":{"type":"string","enum":["completed","rejected","unknown"]}},"required":["simulated","mode","http_status"],"oneOf":[{"required":["data"]},{"required":["error"]}],"additionalProperties":false});
            tools.push(serde_json::from_value(json!({"name":operation.name,"description":description,"inputSchema":operation.input,"outputSchema":output,"annotations":{"readOnlyHint":read_only,"destructiveHint":!read_only,"idempotentHint":read_only,"openWorldHint":true}}))?);
        }
        Ok(Self {
            adapter,
            tools: Arc::new(tools),
        })
    }

    pub async fn invoke(&self, name: &str, args: Value) -> Result<CallToolResult, ErrorData> {
        let Some(helper) = live_helpers()
            .into_iter()
            .find(|helper| helper.name == name)
        else {
            return self.adapter.call(name, args).await;
        };
        let validator = jsonschema::options()
            .with_format("ftth-date-time", live_contract::valid_datetime)
            .should_validate_formats(true)
            .build(&helper.input)
            .map_err(|_| ErrorData::internal_error("invalid_embedded_schema", None))?;
        if args.to_string().len() > 16384 || !validator.is_valid(&args) {
            return Err(ErrorData::invalid_params("invalid_input", None));
        }
        match name {
            "stato_api" => return self.adapter.call("getHealth", args).await,
            "fetch" => {
                let document_id = args["document_id"]
                    .as_str()
                    .ok_or_else(|| ErrorData::invalid_params("invalid_identifier", None))?;
                let (kind, identifier) = document_id
                    .split_once('_')
                    .ok_or_else(|| ErrorData::invalid_params("invalid_identifier", None))?;
                if kind == "material" {
                    return Ok(self.reply(
                        None,
                        Err("ambiguous_material_identifier_use_ont_ID_or_modem_ID"),
                    ));
                }
                let api_id = identifier
                    .parse::<i64>()
                    .ok()
                    .filter(|api_id| *api_id > 0)
                    .ok_or_else(|| ErrorData::invalid_params("invalid_identifier", None))?;
                let (action, parameter) = match kind {
                    "work" => ("getWorkById", "work_id"),
                    "ont" => ("getONTById", "ont_id"),
                    "modem" => ("getModemById", "modem_id"),
                    _ => return Err(ErrorData::invalid_params("invalid_identifier", None)),
                };
                let result = self.adapter.call(action, json!({parameter:api_id})).await?;
                if result.is_error == Some(true) {
                    return Ok(result);
                }
                let envelope = result.structured_content.ok_or_else(|| {
                    ErrorData::internal_error("missing_structured_response", None)
                })?;
                let status = envelope["http_status"]
                    .as_u64()
                    .and_then(|status| u16::try_from(status).ok());
                let record = &envelope["data"];
                if record["id"].as_i64() != Some(api_id) {
                    return Ok(self.reply(status, Err("invalid_response_shape")));
                }
                return Ok(self.reply(
                    status,
                    document(record, kind, false).ok_or("invalid_response_shape"),
                ));
            }
            _ => {}
        }
        if name == "search" {
            let query = args["query"].as_str().unwrap().trim();
            if query.is_empty() || query.chars().any(char::is_control) {
                return Err(ErrorData::invalid_params("invalid_query", None));
            }
        }
        let result = self.adapter.call("getWorks", json!({})).await?;
        if result.is_error == Some(true) {
            return Ok(result);
        }
        let envelope = result
            .structured_content
            .ok_or_else(|| ErrorData::internal_error("missing_structured_response", None))?;
        let Some(works) = envelope["data"].as_array() else {
            return Ok(self.reply(Some(200), Err("invalid_response_shape")));
        };
        match name {
            "cerca_wr" | "stato_wr" => {
                let mut matches = works
                    .iter()
                    .filter(|work| work["numero_wr"] == args["numero_wr"]);
                let Some(work) = matches.next() else {
                    return Ok(self.reply(Some(200), Err("not_found")));
                };
                if matches.next().is_some() {
                    return Ok(self.reply(Some(200), Err("ambiguous")));
                }
                let Some(found) = document(work, "work", false) else {
                    return Ok(self.reply(Some(200), Err("invalid_response_shape")));
                };
                let data = if name == "stato_wr" {
                    json!({"numero_wr":work["numero_wr"],"work_id":found["work_id"],"stato":work["stato"]})
                } else {
                    found
                };
                Ok(self.reply(Some(200), Ok(data)))
            }
            "riepilogo_wr" => {
                let mut counts = std::collections::BTreeMap::<&str, usize>::new();
                for work in works {
                    *counts
                        .entry(work["stato"].as_str().unwrap_or("unknown"))
                        .or_default() += 1;
                }
                let per_stato: Vec<_> = counts
                    .into_iter()
                    .map(|(stato, totale)| json!({"stato":stato,"totale":totale}))
                    .collect();
                Ok(self.reply(
                    Some(200),
                    Ok(json!({"totale":works.len(),"per_stato":per_stato})),
                ))
            }
            "search" => {
                let query = args["query"].as_str().unwrap().trim().to_lowercase();
                let mut results = Vec::new();
                let add_matches = |records: &[Value],
                                   kind: &str,
                                   results: &mut Vec<Value>|
                 -> Result<(), &'static str> {
                    for record in records {
                        if [
                            "numero_wr",
                            "nome_cliente",
                            "indirizzo",
                            "tipo_lavoro",
                            "serial_number",
                            "model",
                            "manufacturer",
                            "location",
                        ]
                        .iter()
                        .any(|field| {
                            record[field]
                                .as_str()
                                .is_some_and(|text| text.to_lowercase().contains(&query))
                        }) {
                            results.push(
                                document(record, kind, true).ok_or("invalid_response_shape")?,
                            );
                        }
                    }
                    Ok(())
                };
                if let Err(error) = add_matches(works, "work", &mut results) {
                    return Ok(self.reply(Some(200), Err(error)));
                }
                for (action, kind) in [("getONTs", "ont"), ("getModems", "modem")] {
                    let result = self.adapter.call(action, json!({})).await?;
                    if result.is_error == Some(true) {
                        return Ok(result);
                    }
                    let envelope = result.structured_content.ok_or_else(|| {
                        ErrorData::internal_error("missing_structured_response", None)
                    })?;
                    let Some(records) = envelope["data"].as_array() else {
                        return Ok(self.reply(Some(200), Err("invalid_response_shape")));
                    };
                    if let Err(error) = add_matches(records, kind, &mut results) {
                        return Ok(self.reply(Some(200), Err(error)));
                    }
                }
                results.truncate(args["limit"].as_u64().unwrap_or(10) as usize);
                Ok(self.reply(Some(200), Ok(json!({"results":results}))))
            }
            _ => Err(ErrorData::invalid_params("unknown_tool", None)),
        }
    }

    fn reply(&self, status: Option<u16>, data: Result<Value, &str>) -> CallToolResult {
        response(status, data, true, self.adapter.adapter.writes_enabled)
    }
}

pub fn live_http_router(server: LiveActionsServer) -> axum::Router {
    use rmcp::transport::streamable_http_server::{
        StreamableHttpServerConfig, StreamableHttpService, session::local::LocalSessionManager,
    };
    let service = StreamableHttpService::new(
        move || Ok(server.clone()),
        LocalSessionManager::default().into(),
        StreamableHttpServerConfig::default(),
    );
    axum::Router::new().nest_service("/mcp", service)
}

impl ServerHandler for LiveActionsServer {
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
        self.invoke(
            &request.name,
            Value::Object(request.arguments.unwrap_or_default()),
        )
        .await
        .map(Into::into)
    }
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
