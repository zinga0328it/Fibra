use chrono::{DateTime, Datelike, NaiveDate};
use rmcp::{ErrorData, RoleServer, ServerHandler, model::*, service::RequestContext};
use serde::Deserialize;
use serde_json::{Value, json};
use std::{
    collections::BTreeMap,
    sync::{Arc, Mutex},
};

const NOW: &str = "2026-10-15T12:00:00Z";

#[derive(Deserialize)]
pub struct Contract {
    pub source_sha256: String,
    pub operations: Vec<Operation>,
}

#[derive(Deserialize)]
pub struct Operation {
    pub name: String,
    pub method: String,
    pub path: String,
    pub input: Value,
    pub responses: BTreeMap<String, Value>,
    #[serde(default)]
    pub parameter_locations: BTreeMap<String, String>,
    #[serde(default)]
    pub parameter_metadata: BTreeMap<String, Value>,
}

pub fn contract() -> Contract {
    serde_json::from_str(include_str!("../contracts/actions.json")).expect("embedded contract")
}

pub(crate) fn helper_operations() -> Vec<Operation> {
    let wr = json!({"type":"string","pattern":"^[0-9]{1,32}$"});
    [
        ("search",json!({"query":{"type":"string","minLength":1,"maxLength":128},"limit":{"type":["integer","null"],"minimum":1,"maximum":20}}),vec!["query"]),
        ("fetch",json!({"document_id":{"type":"string","pattern":"^(work|material)_[0-9]+$"}}),vec!["document_id"]),
        ("cerca_wr",json!({"numero_wr":wr.clone()}),vec!["numero_wr"]),
        ("stato_wr",json!({"numero_wr":wr}),vec!["numero_wr"]),
        ("stato_api",json!({}),vec![]),
        ("riepilogo_wr",json!({}),vec![]),
    ].into_iter().map(|(name,properties,required)|Operation {
        name:name.into(),method:"GET".into(),path:format!("/simulation/{name}"),
        input:json!({"type":"object","properties":properties,"required":required,"additionalProperties":false}),
        responses:BTreeMap::from([("200".into(),json!({"type":"object"}))]),
        parameter_locations:BTreeMap::new(),parameter_metadata:BTreeMap::new(),
    }).collect()
}

#[derive(Clone, Copy, Default)]
pub enum MockAccess {
    #[default]
    Allowed,
    Denied,
    Expired,
    Unavailable,
}

#[derive(Clone)]
struct State {
    works: BTreeMap<i64, Value>,
    modems: BTreeMap<i64, Value>,
    onts: BTreeMap<i64, Value>,
    technicians: BTreeMap<i64, Value>,
    notifications: Vec<i64>,
    next_work: i64,
    next_modem: i64,
    next_ont: i64,
}

fn equipment(id: i64, kind: &str) -> Value {
    let mut value = json!({"id": id, "serial_number": format!("SIM-{kind}-{id}"), "model": "MODEL-SIM", "manufacturer": "SIM", "status": "disponibile", "location": "Magazzino simulato", "work_id": null, "installation_notes": null, "technician_notes": null, "wifi_ssid": null, "wifi_password": null, "created_at": NOW, "updated_at": NOW});
    if kind == "MODEM" {
        value["type"] = json!("ftth");
    } else {
        value["optical_power"] = Value::Null;
    }
    value
}

fn new_work(id: i64) -> Value {
    json!({"id":id,"numero_wr":format!("SIM-{id}"),"operatore":"Operatore Simulato","indirizzo":"Via di Prova 1","nome_cliente":"Cliente Simulato","tipo_lavoro":"Installazione","note":null,"stato":"aperto","data_apertura":NOW,"data_chiusura":null,"tecnico_assegnato":null,"extra_fields":{},"data_appuntamento":null,"note_appuntamento":null,"motivo_rinvio":null})
}

impl Default for State {
    fn default() -> Self {
        let technician = json!({"id":1,"nome":"Davide Simulato","cognome":"Test","telefono":"","telegram_id":null,"squadra":{"id":1,"nome":"Squadra simulata"}});
        let mut work = new_work(7);
        work["numero_wr"] = json!("103579742");
        work["tecnico_assegnato"] = technician.clone();
        work["data_appuntamento"] = json!(NOW);
        let mut closed = new_work(8);
        closed["stato"] = json!("chiuso");
        closed["data_chiusura"] = json!(NOW);
        closed["tecnico_assegnato"] = technician.clone();
        Self {
            works: BTreeMap::from([(7, work), (8, closed)]),
            modems: BTreeMap::from([(1, equipment(1, "MODEM"))]),
            onts: BTreeMap::from([(1, equipment(1, "ONT"))]),
            technicians: BTreeMap::from([(1, technician)]),
            notifications: vec![],
            next_work: 9,
            next_modem: 2,
            next_ont: 2,
        }
    }
}

struct Registered {
    operation: Operation,
    tool: Tool,
    input: jsonschema::Validator,
    output: jsonschema::Validator,
}

#[derive(Clone)]
pub struct ActionsServer {
    catalog: Arc<Vec<Registered>>,
    state: Arc<Mutex<State>>,
    access: MockAccess,
}

impl ActionsServer {
    pub fn new() -> Result<Self, Box<dyn std::error::Error>> {
        let mut catalog = Vec::new();
        for operation in contract().operations.into_iter().chain(helper_operations()) {
            let read_only = operation.method == "GET";
            let response = &operation.responses["200"];
            let output_schema = json!({"type":"object","properties":{"simulated":{"const":true},"http_status":{"type":"integer"},"data":response,"error":{"type":"string"}},"required":["simulated","http_status"],"oneOf":[{"required":["data"]},{"required":["error"]}],"additionalProperties":false});
            let tool = serde_json::from_value(
                json!({"name":operation.name,"description":format!("SIMULAZIONE LOCALE: {} {}. Nessuna API reale. Le scritture cambiano solo la memoria del simulatore.",operation.method,operation.path),"inputSchema":operation.input,"outputSchema":output_schema,"annotations":{"readOnlyHint":read_only,"destructiveHint":!read_only,"idempotentHint":read_only,"openWorldHint":false}}),
            )?;
            let input = jsonschema::options()
                .should_validate_formats(true)
                .build(&operation.input)?;
            let output = jsonschema::options()
                .should_validate_formats(true)
                .build(response)?;
            catalog.push(Registered {
                operation,
                tool,
                input,
                output,
            });
        }
        Ok(Self {
            catalog: Arc::new(catalog),
            state: Arc::new(Mutex::new(State::default())),
            access: MockAccess::Allowed,
        })
    }

    pub fn with_access(mut self, access: MockAccess) -> Self {
        self.access = access;
        self
    }

    pub fn invoke(&self, name: &str, arguments: Value) -> Result<CallToolResult, ErrorData> {
        let registered = self
            .catalog
            .iter()
            .find(|item| item.operation.name == name)
            .ok_or_else(|| ErrorData::invalid_params("unknown_tool", None))?;
        if arguments.to_string().len() > 16384 || !registered.input.is_valid(&arguments) {
            return Err(ErrorData::invalid_params("invalid_input", None));
        }
        match self.access {
            MockAccess::Denied => return Ok(reply(403, Err("forbidden"))),
            MockAccess::Expired => return Ok(reply(401, Err("expired_mock_authorization"))),
            MockAccess::Unavailable => return Ok(reply(503, Err("mock_unavailable"))),
            MockAccess::Allowed => {}
        }
        let mut state = self
            .state
            .lock()
            .map_err(|_| ErrorData::internal_error("mock_state_unavailable", None))?;
        let mut transaction = state.clone();
        match transaction.execute(name, &arguments) {
            Ok(value) => {
                if !registered.output.is_valid(&value) {
                    return Err(ErrorData::internal_error(
                        "mock_output_contract_violation",
                        None,
                    ));
                }
                *state = transaction;
                Ok(reply(200, Ok(value)))
            }
            Err((status, error)) => Ok(reply(status, Err(error))),
        }
    }
}

fn reply(status: u16, result: Result<Value, &str>) -> CallToolResult {
    let (envelope, failed) = match result {
        Ok(data) => (
            json!({"simulated":true,"http_status":status,"data":data}),
            false,
        ),
        Err(error) => (
            json!({"simulated":true,"http_status":status,"error":error}),
            true,
        ),
    };
    let content = vec![ContentBlock::text(envelope.to_string())];
    let mut response = if failed {
        CallToolResult::error(content)
    } else {
        CallToolResult::success(content)
    };
    response.structured_content = Some(envelope);
    response
}

impl ServerHandler for ActionsServer {
    fn get_info(&self) -> ServerConfig {
        ServerConfig::new(ServerCapabilities::builder().enable_tools().build())
    }
    fn get_tool(&self, name: &str) -> Option<Tool> {
        self.catalog
            .iter()
            .find(|item| item.operation.name == name)
            .map(|item| item.tool.clone())
    }
    async fn list_tools(
        &self,
        _request: Option<PaginatedRequestParams>,
        _context: RequestContext<RoleServer>,
    ) -> Result<ListToolsResult, ErrorData> {
        Ok(ListToolsResult {
            tools: self.catalog.iter().map(|item| item.tool.clone()).collect(),
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
        .map(Into::into)
    }
}

type ActionResult = Result<Value, (u16, &'static str)>;
fn identifier(args: &Value, key: &str) -> Result<i64, (u16, &'static str)> {
    args[key]
        .as_i64()
        .filter(|id| *id > 0)
        .ok_or((400, "invalid_identifier"))
}
fn record(records: &BTreeMap<i64, Value>, id: i64) -> ActionResult {
    records.get(&id).cloned().ok_or((404, "not_found"))
}
fn list(records: &BTreeMap<i64, Value>) -> Value {
    Value::Array(records.values().cloned().collect())
}
fn ok() -> Value {
    json!({"ok":true,"message":"Operazione simulata completata"})
}

impl State {
    fn helper(&self, name: &str, args: &Value) -> ActionResult {
        let document = |work: &Value| {
            let mut result = work.clone();
            result["id"] = json!(format!("work_{}", work["id"]));
            result["type"] = json!("work");
            result
        };
        let material = json!({"id":"material_3","type":"material","nome":"ONT Simulato","codice":"TEST-ONT-003","descrizione":"Materiale fittizio per test locali","tipo":"ONT","quantita":4});
        match name {
            "search" => {
                let query = args["query"].as_str().ok_or((400, "invalid_query"))?.trim();
                if query.is_empty() || query.len() > 128 || query.chars().any(char::is_control) {
                    return Err((400, "invalid_query"));
                }
                let query = query.to_lowercase();
                let mut results: Vec<_> = self
                    .works
                    .values()
                    .filter(|work| {
                        ["numero_wr", "indirizzo", "nome_cliente", "tipo_lavoro"]
                            .iter()
                            .any(|field| {
                                work[field]
                                    .as_str()
                                    .is_some_and(|text| text.to_lowercase().contains(&query))
                            })
                    })
                    .map(document)
                    .collect();
                if ["nome", "codice", "descrizione", "tipo"]
                    .iter()
                    .any(|field| {
                        material[field]
                            .as_str()
                            .is_some_and(|text| text.to_lowercase().contains(&query))
                    })
                {
                    results.push(material);
                }
                results.truncate(args["limit"].as_u64().unwrap_or(10) as usize);
                Ok(json!({"results":results}))
            }
            "fetch" => {
                let text = args["document_id"]
                    .as_str()
                    .ok_or((400, "invalid_identifier"))?;
                if text == "material_3" {
                    return Ok(material);
                }
                let id = text
                    .strip_prefix("work_")
                    .and_then(|text| text.parse::<i64>().ok())
                    .ok_or((404, "not_found"))?;
                record(&self.works, id).map(|work| document(&work))
            }
            "cerca_wr" | "stato_wr" => {
                let mut found = self
                    .works
                    .values()
                    .filter(|work| work["numero_wr"] == args["numero_wr"]);
                let work = found.next().ok_or((404, "not_found"))?;
                if found.next().is_some() {
                    return Err((409, "ambiguous"));
                }
                if name == "stato_wr" {
                    Ok(json!({"numero_wr":work["numero_wr"],"stato":work["stato"]}))
                } else {
                    Ok(document(work))
                }
            }
            "stato_api" => Ok(
                json!({"mock_backend":"ok","production_checked":false,"aaa":"not_checked","zinga":"not_checked","alex":"not_checked"}),
            ),
            "riepilogo_wr" => {
                let mut counts: BTreeMap<&str, usize> = BTreeMap::new();
                for work in self.works.values() {
                    *counts
                        .entry(work["stato"].as_str().unwrap_or("unknown"))
                        .or_default() += 1;
                }
                Ok(
                    json!({"totale":self.works.len(),"per_stato":counts.into_iter().map(|(stato,totale)|json!({"stato":stato,"totale":totale})).collect::<Vec<_>>()}),
                )
            }
            _ => Err((400, "unknown_operation")),
        }
    }

    fn patch_work(&mut self, id: i64, body: &Value) -> ActionResult {
        let technician = if let Some(value) = body.get("tecnico_assegnato") {
            Some(record(
                &self.technicians,
                value.as_i64().ok_or((400, "invalid_technician"))?,
            )?)
        } else {
            None
        };
        let work = self.works.get_mut(&id).ok_or((404, "not_found"))?;
        for field in [
            "numero_wr",
            "nome_cliente",
            "indirizzo",
            "operatore",
            "tipo_lavoro",
            "note",
            "stato",
            "extra_fields",
            "data_appuntamento",
            "note_appuntamento",
            "motivo_rinvio",
        ] {
            if let Some(value) = body.get(field) {
                work[field] = value.clone();
            }
        }
        if let Some(value) = body.get("telefono_cliente") {
            work["extra_fields"]["telefono_cliente"] = value.clone();
        }
        if let Some(value) = technician {
            work["tecnico_assegnato"] = value;
        }
        if body.get("stato").is_some() {
            work["data_chiusura"] = if work["stato"] == "chiuso" {
                json!(NOW)
            } else {
                Value::Null
            };
        }
        Ok(work.clone())
    }

    fn execute(&mut self, name: &str, args: &Value) -> ActionResult {
        match name {
            "getHealth" => Ok(json!({"status":"ok","timestamp":NOW})),
            "getWorks" => Ok(list(&self.works)),
            "getWorkById" => record(&self.works, identifier(args, "work_id")?),
            "getTechnicians" => Ok(list(&self.technicians)),
            "getTeams" => Ok(json!([{"id":1,"nome":"Squadra simulata"}])),
            "getDocuments" => Ok(
                json!([{"id":1,"filename":"documento-simulato.pdf","upload_date":NOW,"parsed":true}]),
            ),
            "createManualWork" => {
                let body = &args["body"];
                if body["numero_wr"].as_str().is_none_or(str::is_empty) {
                    return Err((400, "empty_wr"));
                }
                if self
                    .works
                    .values()
                    .any(|work| work["numero_wr"] == body["numero_wr"])
                {
                    return Err((400, "duplicate_wr"));
                }
                let id = self.next_work;
                self.next_work += 1;
                self.works.insert(id, new_work(id));
                let work = self.patch_work(id, body)?;
                Ok(json!({"ok":true,"id":id,"numero_wr":work["numero_wr"]}))
            }
            "updateWork" => self.patch_work(identifier(args, "work_id")?, &args["body"]),
            "deleteWork" => {
                let id = identifier(args, "work_id")?;
                self.works.remove(&id).ok_or((404, "not_found"))?;
                for device in self.modems.values_mut().chain(self.onts.values_mut()) {
                    if device["work_id"] == id {
                        device["work_id"] = Value::Null;
                        device["status"] = json!("disponibile");
                    }
                }
                Ok(ok())
            }
            "assignTechnicianToWork" => self
                .patch_work(
                    identifier(args, "work_id")?,
                    &json!({"tecnico_assegnato":identifier(args,"technician_id")?}),
                )
                .map(|_| ok()),
            "notifyWorkAssignment" => {
                let id = identifier(args, "work_id")?;
                let work = record(&self.works, id)?;
                if work["tecnico_assegnato"].is_null() {
                    return Err((400, "technician_required"));
                }
                self.notifications.push(id);
                Ok(ok())
            }
            "getModems" => Ok(list(&self.modems)),
            "getONTs" => Ok(list(&self.onts)),
            "getModemById" => record(&self.modems, identifier(args, "modem_id")?),
            "getONTById" => record(&self.onts, identifier(args, "ont_id")?),
            "createModem" | "createONT" => {
                let modem = name == "createModem";
                let (records, next) = if modem {
                    (&mut self.modems, &mut self.next_modem)
                } else {
                    (&mut self.onts, &mut self.next_ont)
                };
                let body = &args["body"];
                if body["serial_number"].as_str().is_none_or(str::is_empty) {
                    return Err((400, "empty_serial"));
                }
                if records
                    .values()
                    .any(|device| device["serial_number"] == body["serial_number"])
                {
                    return Err((400, "duplicate_serial"));
                }
                let id = *next;
                *next += 1;
                let mut device = equipment(id, if modem { "MODEM" } else { "ONT" });
                for field in ["serial_number", "model", "manufacturer", "location", "type"] {
                    if let Some(value) = body.get(field) {
                        device[field] = value.clone();
                    }
                }
                records.insert(id, device);
                Ok(json!({"ok":true,"id":id,"serial_number":body["serial_number"]}))
            }
            "updateModem" | "updateONT" | "installModem" | "installONT" => {
                let modem = name.ends_with("Modem");
                let records = if modem {
                    &mut self.modems
                } else {
                    &mut self.onts
                };
                let device = records
                    .get_mut(&identifier(
                        args,
                        if modem { "modem_id" } else { "ont_id" },
                    )?)
                    .ok_or((404, "not_found"))?;
                if name.starts_with("install") {
                    device["status"] = json!("installato");
                    device["updated_at"] = json!(NOW);
                    return Ok(ok());
                }
                for field in [
                    "installation_notes",
                    "technician_notes",
                    "wifi_ssid",
                    "wifi_password",
                    "location",
                ] {
                    if let Some(value) = args["body"].get(field) {
                        device[field] = value.clone();
                    }
                }
                device["updated_at"] = json!(NOW);
                Ok(device.clone())
            }
            "assignModemToWork" | "assignONTToWork" => {
                let work_id = identifier(args, "work_id")?;
                record(&self.works, work_id)?;
                let modem = name == "assignModemToWork";
                let records = if modem {
                    &mut self.modems
                } else {
                    &mut self.onts
                };
                let id = identifier(args, if modem { "modem_id" } else { "ont_id" })?;
                let device = record(records, id)?;
                if (!device["work_id"].is_null() && device["work_id"] != work_id)
                    || records
                        .values()
                        .any(|value| value["id"] != id && value["work_id"] == work_id)
                {
                    return Err((400, "equipment_conflict"));
                }
                let device = records.get_mut(&id).ok_or((404, "not_found"))?;
                device["work_id"] = json!(work_id);
                device["status"] = json!("assegnato");
                Ok(ok())
            }
            "getWorkEquipment" => {
                let id = identifier(args, "work_id")?;
                let work = record(&self.works, id)?;
                Ok(
                    json!({"work_id":id,"modem":self.modems.values().find(|device|device["work_id"]==id),"ont":self.onts.values().find(|device|device["work_id"]==id),"modem_delivered":work["extra_fields"]["modem_delivered"].as_bool().unwrap_or(false),"ont_delivered":work["extra_fields"]["ont_delivered"].as_bool().unwrap_or(false)}),
                )
            }
            "markEquipmentDelivered" => {
                let work = self
                    .works
                    .get_mut(&identifier(args, "work_id")?)
                    .ok_or((404, "not_found"))?;
                for field in ["modem_delivered", "ont_delivered"] {
                    if let Some(value) = args.get(field) {
                        work["extra_fields"][field] = value.clone();
                    }
                }
                Ok(ok())
            }
            "updateAppointment" => {
                let id = identifier(args, "work_id")?;
                let work = self.works.get_mut(&id).ok_or((404, "not_found"))?;
                let mut changes = Vec::new();
                for field in ["data_appuntamento", "note_appuntamento", "motivo_rinvio"] {
                    if let Some(value) = args.get(field) {
                        if work[field] != *value {
                            changes.push(field);
                        }
                        work[field] = value.clone();
                    }
                }
                if work["data_appuntamento"].is_null() {
                    return Err((400, "appointment_required"));
                }
                Ok(
                    json!({"ok":true,"work_id":id,"numero_wr":work["numero_wr"],"data_appuntamento":work["data_appuntamento"],"note_appuntamento":work["note_appuntamento"],"motivo_rinvio":work["motivo_rinvio"],"changes":changes}),
                )
            }
            "getCalendar" => {
                let from = NaiveDate::parse_from_str(
                    args["from"].as_str().ok_or((400, "invalid_date"))?,
                    "%Y-%m-%d",
                )
                .map_err(|_| (400, "invalid_date"))?;
                let to = NaiveDate::parse_from_str(
                    args["to"].as_str().ok_or((400, "invalid_date"))?,
                    "%Y-%m-%d",
                )
                .map_err(|_| (400, "invalid_date"))?;
                if from > to {
                    return Err((400, "invalid_range"));
                }
                let appointments:Vec<_>=self.works.values().filter(|work|{
                    let date=work["data_appuntamento"].as_str().and_then(|text|DateTime::parse_from_rfc3339(text).ok()).map(|date|date.date_naive());
                    date.is_some_and(|date|date>=from&&date<=to) && args.get("stato").is_none_or(|value|value==&work["stato"]) && args.get("tecnico_id").is_none_or(|value|value==&work["tecnico_assegnato"]["id"])
                }).map(|work|json!({"work_id":work["id"],"numero_wr":work["numero_wr"],"nome_cliente":work["nome_cliente"],"indirizzo":work["indirizzo"],"tipo_lavoro":work["tipo_lavoro"],"stato":work["stato"],"data_appuntamento":work["data_appuntamento"],"note_appuntamento":work["note_appuntamento"],"motivo_rinvio":work["motivo_rinvio"],"tecnico":work["tecnico_assegnato"]["nome"],"tecnico_id":work["tecnico_assegnato"]["id"],"telefono_cliente":work["extra_fields"]["telefono_cliente"]})).collect();
                Ok(
                    json!({"from":args["from"],"to":args["to"],"total":appointments.len(),"appointments":appointments}),
                )
            }
            "getWeeklyStats"
            | "getClosedByOperator"
            | "getClosedByTechnician"
            | "getDailyClosedStats"
            | "getYearlyStats" => self.statistics(name),
            _ => self.helper(name, args),
        }
    }

    fn statistics(&self, name: &str) -> ActionResult {
        let today = DateTime::parse_from_rfc3339(NOW)
            .map_err(|_| (500, "mock_clock"))?
            .date_naive();
        let closed: Vec<_> = self
            .works
            .values()
            .filter(|work| work["stato"] == "chiuso")
            .collect();
        if name == "getWeeklyStats" {
            let monday =
                today - chrono::Duration::days(today.weekday().num_days_from_monday() as i64);
            let count = closed
                .iter()
                .filter(|work| {
                    work["data_chiusura"]
                        .as_str()
                        .and_then(|text| DateTime::parse_from_rfc3339(text).ok())
                        .is_some_and(|date| {
                            date.date_naive() >= monday && date.date_naive() <= today
                        })
                })
                .count();
            return Ok(
                json!({"closed_this_week":count,"suspended":self.works.values().filter(|work|work["stato"]=="sospeso").count()}),
            );
        }
        let mut groups: BTreeMap<String, usize> = BTreeMap::new();
        for work in closed {
            let key = match name {
                "getClosedByOperator" => work["operatore"]
                    .as_str()
                    .unwrap_or("Non assegnato")
                    .to_owned(),
                "getClosedByTechnician" => work["tecnico_assegnato"]["nome"]
                    .as_str()
                    .unwrap_or("Non assegnato")
                    .to_owned(),
                _ => {
                    let Some(date) = work["data_chiusura"]
                        .as_str()
                        .and_then(|text| DateTime::parse_from_rfc3339(text).ok())
                    else {
                        continue;
                    };
                    if name == "getYearlyStats" {
                        if date.year() != today.year() {
                            continue;
                        }
                        format!("{}-{:02}-01", date.year(), date.month())
                    } else {
                        date.date_naive().to_string()
                    }
                }
            };
            *groups.entry(key).or_default() += 1;
        }
        let field = match name {
            "getClosedByOperator" => "operatore",
            "getClosedByTechnician" => "tecnico",
            "getYearlyStats" => "month",
            _ => "date",
        };
        Ok(Value::Array(
            groups
                .into_iter()
                .map(|(key, count)| json!({field:key,"closed":count}))
                .collect(),
        ))
    }
}

pub fn actions_http_router(server: ActionsServer) -> axum::Router {
    use rmcp::transport::streamable_http_server::{
        StreamableHttpServerConfig, StreamableHttpService, session::local::LocalSessionManager,
    };
    let service = StreamableHttpService::new(
        move || Ok(server.clone()),
        LocalSessionManager::default().into(),
        StreamableHttpServerConfig::default().with_json_response(true),
    );
    axum::Router::new().nest_service("/mcp", service)
}
