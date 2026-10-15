use std::{error::Error, net::SocketAddr};

use ftth_lia_mcp::server::{LiaServer, mock_http_router};
use rmcp::{ServiceExt, transport::stdio};

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    let arguments: Vec<String> = std::env::args().skip(1).collect();
    match arguments.as_slice() {
        [mode] if mode == "--mock" => {
            let server = LiaServer::mock().serve(stdio()).await?;
            server.waiting().await?;
        }
        [mode, transport, bind] if mode == "--mock" && transport == "--http" => {
            let address: SocketAddr = bind.parse()?;
            if !address.ip().is_loopback() {
                return Err("HTTP mock consentito solo su loopback".into());
            }
            let router = mock_http_router();
            let listener = tokio::net::TcpListener::bind(address).await?;
            eprintln!("Lia Fibra MOCK: http://{}/mcp (nessun accesso alla produzione)", listener.local_addr()?);
            axum::serve(listener, router).with_graceful_shutdown(async {
                let _shutdown = tokio::signal::ctrl_c().await;
            }).await?;
        }
        _ => return Err("Uso: ftth-lia-mcp --mock [--http 127.0.0.1:PORTA]; modalita reale non implementata".into()),
    }
    Ok(())
}