use std::sync::Arc;

use rmcp::{
    ErrorData, ServerHandler,
    handler::server::wrapper::Parameters,
    model::{CallToolResult, ContentBlock},
    schemars, tool, tool_handler, tool_router,
};
use serde::Deserialize;
use serde_json::{Value, json};

use crate::domain::{Document, MockBackend, ReadBackend, ReadError, Work};

#[derive(Debug, Deserialize, schemars::JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct SearchInput {
    pub query: String,
    pub limit: Option<usize>,
}

#[derive(Debug, Deserialize, schemars::JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct FetchInput {
    pub document_id: String,
}

#[derive(Debug, Deserialize, schemars::JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct WrInput {
    pub numero_wr: String,
}

#[derive(Debug, Deserialize, schemars::JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct EmptyInput {}

#[derive(Clone)]
pub struct LiaServer {
    backend: Arc<dyn ReadBackend>,
}

impl LiaServer {
    pub fn mock() -> Self {
        Self { backend: Arc::new(MockBackend::default()) }
    }
}

fn work_value(work: Work) -> Value {
    json!({
        "id": format!("work_{}", work.id),
        "type": "work",
        "numero_wr": work.numero_wr,
        "indirizzo": work.indirizzo,
        "nome_cliente": work.nome_cliente,
        "tipo_lavoro": work.tipo_lavoro,
        "stato": work.stato
    })
}

fn document_value(document: Document) -> Value {
    match document {
        Document::Work(work) => work_value(work),
        Document::Material(material) => json!({
            "id": format!("material_{}", material.id),
            "type": "material",
            "nome": material.nome,
            "codice": material.codice,
            "descrizione": material.descrizione,
            "tipo": material.tipo,
            "quantita": material.quantita
        }),
    }
}

fn result(value: Result<Value, ReadError>) -> Result<CallToolResult, ErrorData> {
    match value {
        Ok(data) => {
            let envelope = json!({"simulated": true, "data": data});
            let mut response = CallToolResult::success(vec![ContentBlock::text(envelope.to_string())]);
            response.structured_content = Some(envelope);
            Ok(response)
        }
        Err(ReadError::InvalidInput) => Err(ErrorData::invalid_params("invalid_input", None)),
        Err(error) => {
            let envelope = json!({"simulated": true, "error": error.code()});
            let mut response = CallToolResult::error(vec![ContentBlock::text(envelope.to_string())]);
            response.structured_content = Some(envelope);
            Ok(response)
        }
    }
}

#[tool_router]
impl LiaServer {
    #[tool(description = "Cerca lavori e materiali per testo. Solo dati SIMULATI; massimo 20 risultati.", annotations(read_only_hint = true, destructive_hint = false, idempotent_hint = true, open_world_hint = false))]
    fn search(&self, Parameters(input): Parameters<SearchInput>) -> Result<CallToolResult, ErrorData> {
        result(self.backend.search(&input.query, input.limit.unwrap_or(10)).map(|documents| {
            json!({"results": documents.into_iter().map(document_value).collect::<Vec<_>>()})
        }))
    }

    #[tool(description = "Legge un lavoro o materiale SIMULATO tramite document_id restituito da search, ad esempio work_7 o material_3. Non usare il numero WR come ID.", annotations(read_only_hint = true, destructive_hint = false, idempotent_hint = true, open_world_hint = false))]
    fn fetch(&self, Parameters(input): Parameters<FetchInput>) -> Result<CallToolResult, ErrorData> {
        result(self.backend.fetch(&input.document_id).map(document_value))
    }

    #[tool(description = "Cerca una WR SIMULATA per numero esatto, passato come stringa, ad esempio 103579742. Non cerca per ID interno.", annotations(read_only_hint = true, destructive_hint = false, idempotent_hint = true, open_world_hint = false))]
    fn cerca_wr(&self, Parameters(input): Parameters<WrInput>) -> Result<CallToolResult, ErrorData> {
        result(self.backend.find_wr(&input.numero_wr).map(work_value))
    }

    #[tool(description = "Legge lo stato di una WR SIMULATA per numero esatto. Non modifica il lavoro.", annotations(read_only_hint = true, destructive_hint = false, idempotent_hint = true, open_world_hint = false))]
    fn stato_wr(&self, Parameters(input): Parameters<WrInput>) -> Result<CallToolResult, ErrorData> {
        result(self.backend.find_wr(&input.numero_wr).map(|work| {
            json!({"numero_wr": work.numero_wr, "stato": work.stato})
        }))
    }

    #[tool(description = "Controlla SOLO il backend simulato locale. NON verifica disponibilita o autenticazione di AAA, ALEX o ZINGA reali.", annotations(read_only_hint = true, destructive_hint = false, idempotent_hint = true, open_world_hint = false))]
    fn stato_api(&self, Parameters(_input): Parameters<EmptyInput>) -> Result<CallToolResult, ErrorData> {
        result(self.backend.health().map(|()| json!({
            "mock_backend": "ok",
            "production_checked": false,
            "aaa": "not_checked",
            "zinga": "not_checked",
            "alex": "not_checked"
        })))
    }

    #[tool(description = "Conta le WR SIMULATE raggruppandole per stato. Non accede al gestionale reale.", annotations(read_only_hint = true, destructive_hint = false, idempotent_hint = true, open_world_hint = false))]
    fn riepilogo_wr(&self, Parameters(_input): Parameters<EmptyInput>) -> Result<CallToolResult, ErrorData> {
        result(self.backend.counts().map(|counts| {
            let totale: usize = counts.iter().map(|(_, count)| count).sum();
            json!({
                "totale": totale,
                "per_stato": counts.into_iter().map(|(stato, totale)| json!({"stato": stato, "totale": totale})).collect::<Vec<_>>()
            })
        }))
    }
}

#[tool_handler(name = "lia-fibra", version = "0.1.0", instructions = "Ambiente di prova: tutti i risultati sono simulati. Non presentarli come dati reali del gestionale. Nessuna scrittura o rotazione chiavi disponibile.")]
impl ServerHandler for LiaServer {}

pub fn mock_http_router() -> axum::Router {
    use rmcp::transport::streamable_http_server::{
        StreamableHttpService, StreamableHttpServerConfig, session::local::LocalSessionManager,
    };
    let service = StreamableHttpService::new(
        || Ok(LiaServer::mock()),
        LocalSessionManager::default().into(),
        StreamableHttpServerConfig::default().with_json_response(true),
    );
    axum::Router::new().nest_service("/mcp", service)
}