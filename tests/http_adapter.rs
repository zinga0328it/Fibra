use axum::{
    Router,
    body::{Body, to_bytes},
    extract::{Request, State},
    http::{HeaderMap, StatusCode},
    response::Response,
};
use ftth_lia_mcp::{
    actions::{ActionsServer, contract},
    http_adapter::{HttpActionsTestServer, HttpTestAdapter, TEST_API_KEY},
};
use rmcp::{
    ServiceExt,
    model::{CallToolResult, ClientConfig},
};
use serde_json::{Value, json};
use std::{
    collections::BTreeMap,
    sync::{Arc, Mutex},
    time::Duration,
};
mod support;
use support::contract_argument;

#[derive(Clone)]
struct Capture {
    requests: Arc<Mutex<Vec<Observed>>>,
    status: u16,
    reply: String,
    delay: Duration,
}
struct Observed {
    method: String,
    path: String,
    query: BTreeMap<String, String>,
    headers: HeaderMap,
    body: Vec<u8>,
}
struct Fixture {
    capture: Capture,
    adapter: HttpTestAdapter,
    task: tokio::task::JoinHandle<()>,
}
impl Drop for Fixture {
    fn drop(&mut self) {
        self.task.abort();
    }
}

async fn record(State(capture): State<Capture>, request: Request) -> Response {
    let (parts, body) = request.into_parts();
    let bytes = to_bytes(body, 1024 * 1024).await.unwrap();
    let url = reqwest::Url::parse(&format!("http://localhost{}", parts.uri)).unwrap();
    capture.requests.lock().unwrap().push(Observed {
        method: parts.method.to_string(),
        path: parts.uri.path().into(),
        query: url.query_pairs().into_owned().collect(),
        headers: parts.headers,
        body: bytes.to_vec(),
    });
    if !capture.delay.is_zero() {
        tokio::time::sleep(capture.delay).await;
    }
    Response::builder()
        .status(StatusCode::from_u16(capture.status).unwrap())
        .header("Content-Type", "application/json")
        .header("Location", "http://192.0.2.1/never-follow")
        .body(Body::from(capture.reply))
        .unwrap()
}

async fn fixture(status: u16, reply: String, delay: Duration) -> Fixture {
    let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
    let address = listener.local_addr().unwrap();
    let capture = Capture {
        requests: Arc::default(),
        status,
        reply,
        delay,
    };
    let router = Router::new().fallback(record).with_state(capture.clone());
    let task = tokio::spawn(async move {
        axum::serve(listener, router).await.unwrap();
    });
    let adapter = HttpTestAdapter::new(address, Duration::from_millis(150)).unwrap();
    Fixture {
        capture,
        adapter,
        task,
    }
}

#[tokio::test]
async fn all_32_actions_send_exact_http_contract() {
    for operation in contract().operations {
        let mut args = contract_argument(&operation.input, "");
        for name in operation.parameter_locations.keys() {
            if args.get(name).is_none() {
                args[name] = contract_argument(&operation.input["properties"][name], name);
            }
        }
        let expected = ActionsServer::new()
            .unwrap()
            .invoke(&operation.name, args.clone())
            .unwrap()
            .structured_content
            .unwrap();
        assert_eq!(expected["http_status"], 200, "{}: {args}", operation.name);
        let fixture = fixture(200, expected["data"].to_string(), Duration::ZERO).await;
        let result = through_mcp(&fixture.adapter, &operation.name, args.clone()).await;
        assert_ne!(
            result.is_error,
            Some(true),
            "{}: {:?}",
            operation.name,
            result.structured_content
        );
        assert_eq!(result.structured_content.unwrap()["data"], expected["data"]);
        let observations = fixture.capture.requests.lock().unwrap();
        assert_eq!(observations.len(), 1);
        let observed = &observations[0];
        assert_eq!(observed.method, operation.method);
        let mut expected_path = operation.path.clone();
        let mut expected_query = BTreeMap::new();
        for (name, location) in &operation.parameter_locations {
            if let Some(value) = args.get(name) {
                let value = value
                    .as_str()
                    .map(str::to_owned)
                    .unwrap_or_else(|| value.to_string());
                if location == "path" {
                    expected_path = expected_path.replace(&format!("{{{name}}}"), &value);
                } else {
                    expected_query.insert(name.clone(), value);
                }
            }
        }
        assert_eq!(observed.path, expected_path, "{}", operation.name);
        assert_eq!(observed.query, expected_query, "{}", operation.name);
        assert_eq!(observed.headers["x-api-key"], TEST_API_KEY);
        assert_eq!(observed.headers["accept"], "application/json");
        assert!(!observed.headers.contains_key("authorization"));
        if let Some(body) = args.get("body") {
            assert_eq!(
                serde_json::from_slice::<Value>(&observed.body).unwrap(),
                *body
            );
            assert_eq!(observed.headers["content-type"], "application/json");
        } else {
            assert!(observed.body.is_empty());
            assert!(!observed.headers.contains_key("content-type"));
        }
    }
}

async fn through_mcp(adapter: &HttpTestAdapter, name: &str, args: Value) -> CallToolResult {
    let (client_io, server_io) = tokio::io::duplex(65536);
    let handler = HttpActionsTestServer::new(adapter.clone()).unwrap();
    let server = tokio::spawn(async move { handler.serve(server_io).await.unwrap() });
    let client = ClientConfig::default().serve(client_io).await.unwrap();
    let server = server.await.unwrap();
    let tools = client.list_all_tools().await.unwrap();
    assert_eq!(tools.len(), 32);
    let tool = tools.iter().find(|tool| tool.name == name).unwrap();
    let metadata = serde_json::to_value(tool).unwrap();
    assert!(metadata["outputSchema"].is_object());
    let request = serde_json::from_value(json!({"name":name,"arguments":args})).unwrap();
    let result = client.call_tool(request).await.unwrap();
    assert!(jsonschema::is_valid(
        &metadata["outputSchema"],
        result.structured_content.as_ref().unwrap()
    ));
    client.cancel().await.unwrap();
    server.cancel().await.unwrap();
    result
}

#[tokio::test]
async fn writes_are_never_retried_on_errors_or_timeouts() {
    let writes: Vec<_> = contract()
        .operations
        .into_iter()
        .filter(|operation| operation.method != "GET")
        .collect();
    assert_eq!(writes.len(), 15);
    for operation in writes {
        for (status, error, delay) in [
            (401, "unauthorized", Duration::ZERO),
            (403, "forbidden", Duration::ZERO),
            (404, "not_found", Duration::ZERO),
            (409, "conflict", Duration::ZERO),
            (422, "invalid_request", Duration::ZERO),
            (503, "upstream_unavailable", Duration::ZERO),
            (302, "redirect_refused", Duration::ZERO),
            (200, "timeout", Duration::from_secs(2)),
        ] {
            let fixture = fixture(
                status,
                "sensitive-backend-error-must-not-leak".into(),
                delay,
            )
            .await;
            let result = fixture
                .adapter
                .call(&operation.name, contract_argument(&operation.input, ""))
                .await
                .unwrap();
            assert_eq!(result.is_error, Some(true), "{} {status}", operation.name);
            let envelope = result.structured_content.unwrap();
            assert_eq!(envelope["error"], error, "{}", operation.name);
            assert!(!envelope.to_string().contains("sensitive-backend"));
            assert!(!envelope.to_string().contains(TEST_API_KEY));
            assert_eq!(
                fixture.capture.requests.lock().unwrap().len(),
                1,
                "{} was retried",
                operation.name
            );
        }
    }
}

#[tokio::test]
async fn malformed_or_wrong_shaped_responses_and_oversized_bodies_are_rejected() {
    for (body, error) in [
        ("not-json".into(), "invalid_json_response"),
        ("[]".into(), "invalid_response_shape"),
        ("x".repeat(1024 * 1024 + 1), "response_too_large"),
    ] {
        let fixture = fixture(200, body, Duration::ZERO).await;
        let result = fixture.adapter.call("getHealth", json!({})).await.unwrap();
        assert_eq!(result.is_error, Some(true));
        assert_eq!(result.structured_content.unwrap()["error"], error);
    }
}

#[tokio::test]
async fn optional_omission_null_and_unknown_body_fields_survive() {
    let fixture = fixture(200, "{}".into(), Duration::ZERO).await;
    let args = json!({"work_id":7,"body":{"extra_fields":{"nullable_value":null},"extension":{"description":"unchanged"},"extension_null":null}});
    let _result = fixture
        .adapter
        .call("updateWork", args.clone())
        .await
        .unwrap();
    assert!(
        fixture
            .adapter
            .call("updateWork", json!({"work_id":7,"body":{"note":null}}))
            .await
            .is_err()
    );
    let requests = fixture.capture.requests.lock().unwrap();
    assert_eq!(requests.len(), 1);
    let body: Value = serde_json::from_slice(&requests[0].body).unwrap();
    assert_eq!(body, args["body"]);
    assert!(body.get("stato").is_none());
}

#[tokio::test]
async fn query_escaping_and_input_validation_precede_network() {
    let fixture = fixture(200, "[]".into(), Duration::ZERO).await;
    let result = fixture
        .adapter
        .call(
            "getWorks",
            json!({"extension":"a & b/#?=+%","other_url":"http://192.0.2.1/ignored-as-target"}),
        )
        .await
        .unwrap();
    assert_ne!(result.is_error, Some(true));
    let invalid = fixture
        .adapter
        .call("getWorkById", json!({"work_id":"../7"}))
        .await;
    assert!(invalid.is_err());
    assert!(
        fixture
            .adapter
            .call("arbitrary_url", json!({}))
            .await
            .is_err()
    );
    let requests = fixture.capture.requests.lock().unwrap();
    assert_eq!(requests.len(), 1);
    assert_eq!(requests[0].query["extension"], "a & b/#?=+%");
    assert_eq!(requests[0].path, "/works/");
}

#[test]
fn non_loopback_targets_are_rejected() {
    for address in [
        "192.0.2.1:80",
        "0.0.0.0:8000",
        "[::]:8000",
        "[::ffff:192.0.2.1]:80",
        "127.0.0.1:0",
    ] {
        assert!(HttpTestAdapter::new(address.parse().unwrap(), Duration::from_secs(1)).is_err());
    }
}

#[tokio::test]
async fn connection_failure_is_sanitized() {
    let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
    let address = listener.local_addr().unwrap();
    drop(listener);
    let adapter = HttpTestAdapter::new(address, Duration::from_millis(150)).unwrap();
    let result = adapter.call("getHealth", json!({})).await.unwrap();
    assert_eq!(
        result.structured_content.unwrap()["error"],
        "transport_unavailable"
    );
}
