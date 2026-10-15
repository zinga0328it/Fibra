use std::time::Duration;

use ftth_lia_mcp::server::mock_http_router;
use rmcp::{
    RoleClient, ServiceExt,
    model::{CallToolRequestParams, ClientConfig},
    service::RunningService,
    transport::{StreamableHttpClientTransport, TokioChildProcess},
};
use serde_json::{Value, json};
mod support;
use support::contract_argument;

fn request(name: &str, arguments: Value) -> CallToolRequestParams {
    serde_json::from_value(json!({"name": name, "arguments": arguments})).unwrap()
}

async fn call(
    client: &RunningService<RoleClient, ClientConfig>,
    name: &str,
    arguments: Value,
) -> Value {
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
    assert_eq!(
        names,
        [
            "cerca_wr",
            "fetch",
            "riepilogo_wr",
            "search",
            "stato_api",
            "stato_wr"
        ]
    );
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
        (
            "stato_wr",
            json!({"numero_wr": "103579742", "stato": "chiuso"}),
        ),
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

    let missing = client
        .call_tool(request("cerca_wr", json!({"numero_wr": "999999999"})))
        .await
        .unwrap();
    assert_eq!(missing.is_error, Some(true));
    assert_eq!(missing.structured_content.unwrap()["error"], "not_found");
    assert_eq!(
        call(client, "fetch", json!({"document_id": "work_7"})).await,
        work
    );
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
    })
    .await
    .expect("stdio MCP test timeout");
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
    })
    .await;
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
        vec!["--mock-actions", "--http", "0.0.0.0:6032"],
        vec!["--mock-actions", "--http", "[::]:6032"],
        vec!["--dev-read", "--http", "127.0.0.1:6032"],
        vec!["--dev-read", "/home/aaa/fibra"],
    ] {
        let output = std::process::Command::new(env!("CARGO_BIN_EXE_ftth-lia-mcp"))
            .args(arguments)
            .output()
            .unwrap();
        assert!(!output.status.success());
        assert!(output.stdout.is_empty());
    }
}

async fn exercise_actions(client: &RunningService<RoleClient, ClientConfig>) {
    let tools = client.list_all_tools().await.unwrap();
    assert_eq!(tools.len(), 38);
    let contract = ftth_lia_mcp::actions::contract();
    for operation in &contract.operations {
        let tool = tools
            .iter()
            .find(|tool| tool.name == operation.name)
            .unwrap();
        let metadata = serde_json::to_value(tool).unwrap();
        assert_eq!(metadata["inputSchema"], operation.input);
        assert!(metadata["outputSchema"].is_object());
        assert_eq!(
            metadata["annotations"]["readOnlyHint"],
            operation.method == "GET"
        );
        assert_eq!(
            metadata["annotations"]["destructiveHint"],
            operation.method != "GET"
        );
    }
    let health = call(client, "stato_api", json!({})).await;
    assert_eq!(health["production_checked"], false);
    for (name, args) in [
        ("search", json!({"query":"103579742"})),
        ("fetch", json!({"document_id":"work_7"})),
        ("cerca_wr", json!({"numero_wr":"103579742"})),
        ("stato_wr", json!({"numero_wr":"103579742"})),
        ("riepilogo_wr", json!({})),
    ] {
        call(client, name, args).await;
    }
    let mut operations = contract.operations;
    operations.sort_by_key(|operation| operation.name == "deleteWork");
    for operation in operations {
        let args = contract_argument(&operation.input, "");
        let result = call(client, &operation.name, args).await;
        assert!(
            jsonschema::is_valid(&operation.responses["200"], &result),
            "{}",
            operation.name
        );
        if let Some(field) = operation.input["required"]
            .as_array()
            .and_then(|fields| fields.first())
            .and_then(Value::as_str)
        {
            let mut invalid_args = contract_argument(&operation.input, "");
            invalid_args[field] = Value::Null;
            let invalid = client
                .call_tool(request(&operation.name, invalid_args))
                .await;
            assert!(invalid.is_err() || invalid.unwrap().is_error == Some(true));
        }
    }
    for name in ["project_write", "ruota_chiavi", "execute_sql"] {
        assert!(client.call_tool(request(name, json!({}))).await.is_err());
    }
}

#[tokio::test]
async fn all_38_tools_over_stdio() {
    tokio::time::timeout(Duration::from_secs(20), async {
        let mut command = tokio::process::Command::new(env!("CARGO_BIN_EXE_ftth-lia-mcp"));
        command.arg("--mock-actions").kill_on_drop(true);
        let transport = TokioChildProcess::new(command).unwrap();
        let client = ClientConfig::default().serve(transport).await.unwrap();
        exercise_actions(&client).await;
        client.cancel().await.unwrap();
    })
    .await
    .expect("Actions stdio timeout");
}

#[tokio::test]
async fn development_read_and_diff_over_stdio_without_write_tools() {
    tokio::time::timeout(Duration::from_secs(15),async {
        let mut command=tokio::process::Command::new(env!("CARGO_BIN_EXE_ftth-lia-mcp"));
        command.arg("--dev-read").kill_on_drop(true);
        let client=ClientConfig::default().serve(TokioChildProcess::new(command).unwrap()).await.unwrap();
        let tools=client.list_all_tools().await.unwrap();
        assert_eq!(tools.len(),2);
        for tool in &tools {
            assert!(["project_read","project_diff"].contains(&tool.name.as_ref()));
            let metadata=serde_json::to_value(tool).unwrap();
            assert!(metadata["outputSchema"].is_object());
            assert_eq!(metadata["annotations"]["readOnlyHint"],true);
        }
        let read=client.call_tool(request("project_read",json!({"path":"src/lib.rs"}))).await.unwrap().structured_content.unwrap();
        assert_eq!(read["read_only"],true);
        let diff=client.call_tool(request("project_diff",json!({"path":"src/lib.rs","expected_sha256":read["sha256"],"proposed_content":"preview only\n"}))).await.unwrap().structured_content.unwrap();
        assert!(diff["diff"].as_str().unwrap().contains("+preview only"));
        let unchanged=client.call_tool(request("project_read",json!({"path":"src/lib.rs"}))).await.unwrap().structured_content.unwrap();
        assert_eq!(unchanged,read);
        for name in ["project_write","project_test","project_commit","execute_shell"] {
            assert!(client.call_tool(request(name,json!({}))).await.is_err());
        }
        let rejected=client.call_tool(request("project_read",json!({"path":"../fibra/.env"}))).await;
        assert!(rejected.is_err() || rejected.unwrap().is_error==Some(true));
        client.cancel().await.unwrap();
    }).await.expect("development stdio timeout");
}

#[tokio::test]
async fn all_38_tools_over_http() {
    let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
    let address = listener.local_addr().unwrap();
    let state = ftth_lia_mcp::actions::ActionsServer::new().unwrap();
    let router = ftth_lia_mcp::actions::actions_http_router(state);
    let server = tokio::spawn(async move {
        axum::serve(listener, router).await.unwrap();
    });
    let outcome = tokio::time::timeout(Duration::from_secs(20), async {
        let transport = StreamableHttpClientTransport::from_uri(format!("http://{address}/mcp"));
        let client = ClientConfig::default().serve(transport).await.unwrap();
        exercise_actions(&client).await;
        client.cancel().await.unwrap();
    })
    .await;
    server.abort();
    let _shutdown = server.await;
    outcome.expect("Actions HTTP timeout");
}
