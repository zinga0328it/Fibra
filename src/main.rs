use std::{error::Error, net::SocketAddr};

use ftth_lia_mcp::actions::{ActionsServer, actions_http_router};
use ftth_lia_mcp::server::{LiaServer, mock_http_router};
use rmcp::{ServiceExt, transport::stdio};

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    let arguments: Vec<String> = std::env::args().skip(1).collect();
    match arguments.as_slice() {
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
        _ => return Err("Uso: ftth-lia-mcp (--mock | --mock-actions) [--http 127.0.0.1:PORTA] oppure --dev-read (solo stdio); API reali non abilitate".into()),
    }
    Ok(())
}
