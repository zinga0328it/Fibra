use std::time::Duration;

use ftth_lia_mcp::server::mock_http_router;
use rmcp::{
    RoleClient, ServiceExt,
    model::{CallToolRequestParams, ClientConfig},
    service::RunningService,
    transport::{StreamableHttpClientTransport, TokioChildProcess},
};
use serde_json::{Value, json};

fn request(name: &str, arguments: Value) -> CallToolRequestParams {
    serde_json::from_value(json!({"name": name, "arguments": arguments})).unwrap()
}

async fn call(client: &RunningService<RoleClient, ClientConfig>, name: &str, arguments: Value) -> Value {
    let response = client.call_tool(request(name, arguments)).await.unwrap();
    assert!(!response.is_error.unwrap_or(false));
    let result = response.structured_content.unwrap();
    assert_eq!(result["simulated"], true);
    result["data"].clone()
}

async fn exercise(client: &RunningService<RoleClient, ClientConfig>) {
    let tools = client.list_all_tools().await.unwrap();
    let mut names: Vec<_> = tools.iter().map(|tool| tool.name.as_ref()).collect();
    names.sort_unstable();
    assert_eq!(names, ["cerca_wr", "fetch", "riepilogo_wr", "search", "stato_api", "stato_wr"]);
    for tool in tools {
        let metadata = serde_json::to_value(tool).unwrap();
        assert_eq!(metadata["annotations"]["readOnlyHint"], true);
        assert_eq!(metadata["annotations"]["destructiveHint"], false);
        assert!(metadata["inputSchema"].is_object());
    }

    let results = call(client, "search", json!({"query": "simulato", "limit": 20})).await;
    assert_eq!(results["results"].as_array().unwrap().len(), 3);
    let limited = call(client, "search", json!({"query": "simulato", "limit": 1})).await;
    assert_eq!(limited["results"].as_array().unwrap().len(), 1);
    let empty = call(client, "search", json!({"query": "inesistente"})).await;
    assert_eq!(empty["results"], json!([]));
    let work = call(client, "fetch", json!({"document_id": "work_7"})).await;
    assert_eq!(work["numero_wr"], "103579742");
    let material = call(client, "fetch", json!({"document_id": "material_3"})).await;
    assert_eq!(material["quantita"], 4);
    let found = call(client, "cerca_wr", json!({"numero_wr": "103579742"})).await;
    assert_eq!(found, work);
    let status = call(client, "stato_wr", json!({"numero_wr": "103579742"})).await;
    assert_eq!(status["stato"], "aperto");
    let health = call(client, "stato_api", json!({})).await;
    assert_eq!(health["production_checked"], false);
    assert_eq!(health["zinga"], "not_checked");
    let summary = call(client, "riepilogo_wr", json!({})).await;
    assert_eq!(summary["totale"], 2);

    for (name, arguments) in [
        ("search", json!({"query": ""})),
        ("search", json!({"query": "test", "limit": 21})),
        ("fetch", json!({"document_id": "https://example.com"})),
        ("cerca_wr", json!({"numero_wr": 103579742})),
        ("stato_wr", json!({"numero_wr": "103579742", "stato": "chiuso"})),
        ("stato_api", json!({"url": "https://example.com"})),
        ("riepilogo_wr", json!({"command": "delete"})),
        ("chiudi_wr", json!({"numero_wr": "103579742"})),
        ("ruota_chiavi", json!({})),
    ] {
        let rejected = match client.call_tool(request(name, arguments)).await {
            Err(_) => true,
            Ok(response) => response.is_error == Some(true),
        };
        assert!(rejected, "{name} accepted invalid input");
    }

    let missing = client.call_tool(request("cerca_wr", json!({"numero_wr": "999999999"}))).await.unwrap();
    assert_eq!(missing.is_error, Some(true));
    assert_eq!(missing.structured_content.unwrap()["error"], "not_found");
    assert_eq!(call(client, "fetch", json!({"document_id": "work_7"})).await, work);
}

#[tokio::test]
async fn all_tools_over_stdio() {
    tokio::time::timeout(Duration::from_secs(15), async {
        let mut command = tokio::process::Command::new(env!("CARGO_BIN_EXE_ftth-lia-mcp"));
        command.arg("--mock").kill_on_drop(true);
        let transport = TokioChildProcess::new(command).unwrap();
        let client = ClientConfig::default().serve(transport).await.unwrap();
        exercise(&client).await;
        client.cancel().await.unwrap();
    }).await.expect("stdio MCP test timeout");
}

#[tokio::test]
async fn all_tools_over_streamable_http() {
    let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
    let address = listener.local_addr().unwrap();
    let server = tokio::spawn(async move {
        axum::serve(listener, mock_http_router()).await.unwrap();
    });
    let outcome = tokio::time::timeout(Duration::from_secs(15), async {
        let transport = StreamableHttpClientTransport::from_uri(format!("http://{address}/mcp"));
        let client = ClientConfig::default().serve(transport).await.unwrap();
        exercise(&client).await;
        client.cancel().await.unwrap();
    }).await;
    server.abort();
    let _shutdown = server.await;
    outcome.expect("HTTP MCP test timeout");
}

#[test]
fn unsafe_or_implicit_startup_is_rejected() {
    for arguments in [
        vec![],
        vec!["--real"],
        vec!["--mock", "--http", "0.0.0.0:6032"],
        vec!["--mock", "--http", "[::]:6032"],
    ] {
        let output = std::process::Command::new(env!("CARGO_BIN_EXE_ftth-lia-mcp"))
            .args(arguments).output().unwrap();
        assert!(!output.status.success());
        assert!(output.stdout.is_empty());
    }
}