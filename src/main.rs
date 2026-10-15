use std::{error::Error, net::SocketAddr};

use ftth_lia_mcp::actions::{ActionsServer, actions_http_router};
use ftth_lia_mcp::http_adapter::{LiveActionsServer, ProductionAdapter, live_http_router};
use ftth_lia_mcp::server::{LiaServer, mock_http_router};
use rmcp::{ServiceExt, transport::stdio};

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    let arguments: Vec<String> = std::env::args().skip(1).collect();
    match arguments.as_slice() {
        [mode] if mode == "--check-live" => {
            let _verified = verified_live_server(false).await?;
        }
        [mode, transport, bind] if (mode == "--live-read-only" || mode == "--live") && transport == "--http" => {
            let address: SocketAddr = bind.parse()?;
            if !address.ip().is_loopback() || address.port() == 0 {
                return Err("HTTP reale consentito solo su loopback e porta esplicita".into());
            }
            let listener = tokio::net::TcpListener::bind(address).await?;
            let writes_enabled = mode == "--live";
            let server = verified_live_server(writes_enabled).await?;
            eprintln!("Lia Fibra LIVE: http://{}/mcp; health verificata; scritture {}", listener.local_addr()?, if writes_enabled { "abilitate" } else { "bloccate" });
            axum::serve(listener, live_http_router(server)).with_graceful_shutdown(async {
                let _shutdown = tokio::signal::ctrl_c().await;
            }).await?;
        }
        [mode] if mode == "--dev-read" => {
            let server = ftth_lia_mcp::project::ProjectServer::open(std::path::Path::new(env!("CARGO_MANIFEST_DIR")))?
                .serve(stdio()).await?;
            server.waiting().await?;
        }
        [mode] if mode == "--mock" => {
            let server = LiaServer::mock().serve(stdio()).await?;
            server.waiting().await?;
        }
        [mode] if mode == "--mock-actions" => {
            let server = ActionsServer::new()?.serve(stdio()).await?;
            server.waiting().await?;
        }
        [mode, transport, bind] if (mode == "--mock" || mode == "--mock-actions") && transport == "--http" => {
            let address: SocketAddr = bind.parse()?;
            if !address.ip().is_loopback() {
                return Err("HTTP mock consentito solo su loopback".into());
            }
            let router = if mode == "--mock-actions" { actions_http_router(ActionsServer::new()?) } else { mock_http_router() };
            let listener = tokio::net::TcpListener::bind(address).await?;
            eprintln!("Lia Fibra MOCK: http://{}/mcp (nessun accesso alla produzione)", listener.local_addr()?);
            axum::serve(listener, router).with_graceful_shutdown(async {
                let _shutdown = tokio::signal::ctrl_c().await;
            }).await?;
        }
        _ => return Err("Uso: ftth-lia-mcp (--mock | --mock-actions) [--http 127.0.0.1:PORTA], --dev-read (solo stdio), --check-live, oppure (--live | --live-read-only) --http 127.0.0.1:PORTA; i profili reali richiedono FTTH_API_KEY nell'ambiente".into()),
    }
    Ok(())
}

async fn verified_live_server(writes_enabled: bool) -> Result<LiveActionsServer, Box<dyn Error>> {
    let api_key = std::env::var("FTTH_API_KEY")
        .map_err(|_| "FTTH_API_KEY richiesta nell'ambiente; non passarla negli argomenti")?;
    let adapter = if writes_enabled {
        ProductionAdapter::read_write(api_key)?
    } else {
        ProductionAdapter::new(api_key)?
    };
    let server = LiveActionsServer::new(adapter)?;
    let result = server.invoke("stato_api", serde_json::json!({})).await?;
    let envelope = result
        .structured_content
        .as_ref()
        .ok_or("missing_structured_response")?;
    eprintln!(
        "Verifica API reale: HTTP {}; errore {}",
        envelope["http_status"], envelope["error"]
    );
    if result.is_error == Some(true) {
        return Err(
            "Avvio annullato: verifica API reale non riuscita; nessun fallback al simulatore"
                .into(),
        );
    }
    Ok(server)
}
