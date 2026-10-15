use crate::actions::Operation;
use serde_json::{Value, json};

pub(super) fn prepare_arguments(name: &str, args: &mut Value) -> Result<(), &'static str> {
    if matches!(name, "updateWork" | "createManualWork")
        && let Some(body) = args.get_mut("body").and_then(Value::as_object_mut)
        && let Some(legacy) = body.remove("tecnico_assegnato")
    {
        if body
            .get("tecnico_assegnato_id")
            .is_some_and(|current| current != &legacy)
        {
            return Err("conflicting_technician_identifiers");
        }
        body.insert("tecnico_assegnato_id".into(), legacy);
    }
    Ok(())
}

pub(super) fn valid_datetime(value: &str) -> bool {
    chrono::DateTime::parse_from_rfc3339(value).is_ok()
        || chrono::NaiveDateTime::parse_from_str(value, "%Y-%m-%dT%H:%M:%S%.f").is_ok()
        || chrono::NaiveDateTime::parse_from_str(value, "%Y-%m-%dT%H:%M").is_ok()
}

fn nullable(schema: &mut Value) {
    if !jsonschema::is_valid(schema, &Value::Null) {
        *schema = json!({"anyOf":[schema.clone(),{"type":"null"}]});
    }
}

fn timestamps(schema: &mut Value) {
    if schema.get("format").and_then(Value::as_str) == Some("date-time") {
        schema["format"] = json!("ftth-date-time");
    }
    match schema {
        Value::Object(fields) => fields.values_mut().for_each(timestamps),
        Value::Array(items) => items.iter_mut().for_each(timestamps),
        _ => {}
    }
}

fn responses(schema: &mut Value) {
    if let Some(properties) = schema.get_mut("properties").and_then(Value::as_object_mut) {
        if properties.contains_key("numero_wr") && properties.contains_key("data_appuntamento") {
            for name in [
                "operatore",
                "indirizzo",
                "nome_cliente",
                "tipo_lavoro",
                "stato",
                "data_apertura",
                "data_chiusura",
                "data_appuntamento",
                "extra_fields",
            ] {
                if let Some(field) = properties.get_mut(name) {
                    if name == "stato" {
                        *field = json!({"type":"string"});
                    }
                    nullable(field);
                }
            }
            if properties.contains_key("motivo_rinvio") {
                properties.insert("motivo_rinvio".into(), json!({"type":["string","null"]}));
            }
        }
        if properties.contains_key("serial_number") {
            for name in ["manufacturer", "location"] {
                if let Some(field) = properties.get_mut(name) {
                    nullable(field);
                }
            }
            for name in ["status", "type"] {
                if properties.contains_key(name) {
                    properties.insert(name.into(), json!({"type":"string"}));
                }
            }
        }
        if properties.contains_key("cognome")
            && let Some(squadra) = properties.get_mut("squadra")
        {
            nullable(squadra);
        }
    }
    match schema {
        Value::Object(fields) => fields.values_mut().for_each(responses),
        Value::Array(items) => items.iter_mut().for_each(responses),
        _ => {}
    }
}

pub(super) fn adapt(operation: &mut Operation) {
    match operation.name.as_str() {
        "getYearlyStats" => {
            operation.responses.insert("200".into(), json!({"type":"array","items":{"type":"object","properties":{"date":{"type":"string","pattern":"^[0-9]{4}-(0[1-9]|1[0-2])$"},"closed":{"type":"integer"}},"required":["date","closed"]}}));
        }
        "getDailyClosedStats" => {
            operation.responses.get_mut("200").unwrap()["items"]["properties"]["date"] =
                json!({"type":"string"});
        }
        "getDocuments" => {
            let properties = operation.responses.get_mut("200").unwrap()["items"]["properties"]
                .as_object_mut()
                .unwrap();
            properties.insert(
                "uploaded_at".into(),
                json!({"anyOf":[{"type":"string","format":"date-time"},{"type":"null"}]}),
            );
            properties.insert("parsed_data".into(), json!({"type":["object","null"]}));
            properties.insert("applied_work_id".into(), json!({"type":["integer","null"]}));
        }
        "updateWork" => {
            let body = &mut operation.input["properties"]["body"];
            body["additionalProperties"] = json!(false);
            let properties = body["properties"].as_object_mut().unwrap();
            properties.insert("extra_fields".into(), json!({"type":["object","null"]}));
            for name in [
                "numero_wr",
                "operatore",
                "indirizzo",
                "nome_cliente",
                "tipo_lavoro",
                "note",
                "note_appuntamento",
                "telefono_cliente",
                "modem_sn",
                "note_chiusura",
            ] {
                properties.insert(name.into(), json!({"type":["string","null"]}));
            }
            properties.insert(
                "tecnico_assegnato_id".into(),
                json!({"type":["integer","null"],"minimum":1}),
            );
            for name in [
                "requires_modem",
                "requires_ont",
                "modem_delivered",
                "ont_delivered",
            ] {
                properties.insert(name.into(), json!({"type":"boolean"}));
            }
            properties.insert("stato".into(), json!({"type":"string","enum":["aperto","in_corso","sospeso","chiuso","attivato","non attivato","non_attivato","assegnata","assegnato"]}));
            nullable(properties.get_mut("data_appuntamento").unwrap());
            nullable(properties.get_mut("motivo_rinvio").unwrap());
        }
        "createManualWork" => {
            let properties = operation.input["properties"]["body"]["properties"]
                .as_object_mut()
                .unwrap();
            properties.insert(
                "tecnico_assegnato_id".into(),
                json!({"type":"integer","minimum":1}),
            );
            properties.insert("tipo_lavoro".into(), json!({"type":"string"}));
            properties.insert("stato".into(), json!({"type":"string"}));
            properties.insert("extra_fields".into(), json!({"type":["object","null"]}));
            properties.insert("note".into(), json!({"type":["string","null"]}));
        }
        "createModem" | "updateModem" | "createONT" | "updateONT" => {
            let modem = operation.name.ends_with("Modem");
            let create = operation.name.starts_with("create");
            let body = &mut operation.input["properties"]["body"];
            body["additionalProperties"] = json!(false);
            let properties = body["properties"].as_object_mut().unwrap();
            if modem {
                properties.remove("technician_notes");
                for name in [
                    "wifi_ssid",
                    "wifi_password",
                    "admin_username",
                    "admin_password",
                    "sync_method",
                    "configuration_notes",
                ] {
                    properties.insert(name.into(), json!({"type":["string","null"]}));
                }
                properties.insert("sync_config".into(), json!({"type":["object","null"]}));
                if create {
                    properties.insert("type".into(), json!({"type":"string","minLength":1}));
                }
            } else {
                properties.remove("wifi_ssid");
                properties.remove("wifi_password");
                for name in ["pon_port", "ip_address", "technician_notes"] {
                    properties.insert(name.into(), json!({"type":["string","null"]}));
                }
                properties.insert("vlan_id".into(), json!({"type":["integer","null"]}));
            }
            for name in ["installation_notes", "location"] {
                properties.insert(name.into(), json!({"type":["string","null"]}));
            }
            if create {
                properties.insert("manufacturer".into(), json!({"type":["string","null"]}));
            } else {
                properties.insert("status".into(), json!({"type":"string"}));
            }
        }
        "getModems" | "getONTs" => {
            operation.input["properties"]["status"] = json!({"type":"string"});
            if operation.name == "getModems" {
                operation.input["properties"]["type"] = json!({"type":"string"});
            }
        }
        _ => {}
    }
    for (name, location) in &operation.parameter_locations {
        if location == "path" && operation.input["properties"][name]["type"] == "integer" {
            operation.input["properties"][name]["minimum"] = json!(1);
        }
    }
    timestamps(&mut operation.input);
    for schema in operation.responses.values_mut() {
        responses(schema);
        timestamps(schema);
    }
}
