use serde_json::{Value, json};

pub fn contract_argument(schema: &Value, name: &str) -> Value {
    if let Some(default) = schema.get("default") {
        return default.clone();
    }
    if let Some(first) = schema["enum"].as_array().and_then(|values| values.first()) {
        return first.clone();
    }
    if let Some(first) = schema["anyOf"]
        .as_array()
        .and_then(|values| values.iter().find(|value| value["type"] != "null"))
    {
        return contract_argument(first, name);
    }
    match schema["type"].as_str().unwrap_or("object") {
        "integer" => json!(if name == "work_id" { 7 } else { 1 }),
        "boolean" => json!(true),
        "string" => json!(match schema["format"].as_str() {
            Some("date") => "2026-10-15",
            Some("date-time") => "2026-10-15T12:00:00Z",
            _ => "SIM-PROTOCOL",
        }),
        "array" => json!([]),
        _ => {
            let mut value = json!({});
            if let Some(required) = schema["required"].as_array() {
                for field in required {
                    let field = field.as_str().unwrap();
                    value[field] = contract_argument(&schema["properties"][field], field);
                }
            }
            value
        }
    }
}
