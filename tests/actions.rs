use ftth_lia_mcp::actions::{ActionsServer, MockAccess, contract};
use serde_json::{Value, json};

fn sample(name: &str) -> Value {
    match name {
        "createManualWork" => {
            json!({"body":{"numero_wr":"SIM-NEW","operatore":"Simulato","indirizzo":"Via di Prova 3","data_appuntamento":"2026-10-16T10:00:00Z"}})
        }
        "updateWork" => json!({"work_id":7,"body":{"stato":"sospeso","note":"Nota simulata"}}),
        "createModem" => {
            json!({"body":{"serial_number":"SIM-NEW-MODEM","model":"MODEL","type":"ftth"}})
        }
        "createONT" => json!({"body":{"serial_number":"SIM-NEW-ONT","model":"MODEL"}}),
        "updateModem" => json!({"modem_id":1,"body":{"location":"Deposito simulato"}}),
        "updateONT" => json!({"ont_id":1,"body":{"location":"Deposito simulato"}}),
        "getCalendar" => json!({"from":"2026-10-01","to":"2026-10-31"}),
        "updateAppointment" => {
            json!({"work_id":7,"data_appuntamento":"2026-10-16T11:00:00Z","note_appuntamento":"Test","motivo_rinvio":"pioggia"})
        }
        "markEquipmentDelivered" => {
            json!({"work_id":7,"modem_delivered":true,"ont_delivered":true})
        }
        _ => {
            let operation = contract()
                .operations
                .into_iter()
                .find(|operation| operation.name == name)
                .unwrap();
            let mut args = json!({});
            for key in operation.input["required"].as_array().unwrap() {
                let key = key.as_str().unwrap();
                args[key] = json!(if key == "work_id" { 7 } else { 1 });
            }
            args
        }
    }
}

fn invoke(server: &ActionsServer, name: &str, args: Value) -> Value {
    let result = server
        .invoke(name, args)
        .unwrap_or_else(|error| panic!("{name}: {error}"));
    let value = result.structured_content.unwrap();
    assert_eq!(value["simulated"], true);
    value
}

fn data(server: &ActionsServer, name: &str, args: Value) -> Value {
    let value = invoke(server, name, args);
    assert_eq!(value["http_status"], 200, "{name}: {value}");
    value["data"].clone()
}

macro_rules! regression {
    ($($name:ident),+ $(,)?)=>{$(
        #[test]
        #[allow(non_snake_case)]
        fn $name() {
            let server=ActionsServer::new().unwrap();
            let name=stringify!($name);
            let result=data(&server,name,sample(name));
            let operation=contract().operations.into_iter().find(|operation|operation.name==name).unwrap();
            assert!(jsonschema::is_valid(&operation.responses["200"],&result));
            let mut extra=sample(name); extra["untrusted_url"]=json!("http://example.invalid");
            assert!(server.invoke(name,extra).is_ok());
            for key in operation.input["required"].as_array().unwrap() {
                let mut missing=sample(name); missing.as_object_mut().unwrap().remove(key.as_str().unwrap());
                assert!(server.invoke(name,missing).is_err());
            }
        }
    )+};
}

regression!(
    getHealth,
    getWorks,
    getWorkById,
    updateWork,
    deleteWork,
    createManualWork,
    getTechnicians,
    getTeams,
    getWeeklyStats,
    getClosedByOperator,
    getClosedByTechnician,
    getDailyClosedStats,
    getYearlyStats,
    getDocuments,
    getModems,
    createModem,
    getModemById,
    updateModem,
    installModem,
    assignModemToWork,
    getWorkEquipment,
    markEquipmentDelivered,
    getONTs,
    createONT,
    getONTById,
    updateONT,
    installONT,
    assignONTToWork,
    notifyWorkAssignment,
    assignTechnicianToWork,
    getCalendar,
    updateAppointment
);

#[test]
fn contract_inventory_is_exact() {
    let contract = contract();
    assert_eq!(contract.operations.len(), 32);
    assert_eq!(contract.source_sha256.len(), 64);
    assert_eq!(
        contract
            .operations
            .iter()
            .filter(|operation| operation.method == "GET")
            .count(),
        17
    );
    assert_eq!(
        contract
            .operations
            .iter()
            .map(|operation| &operation.name)
            .collect::<std::collections::BTreeSet<_>>()
            .len(),
        32
    );
}

#[test]
fn all_actions_fail_closed_on_simulated_denial_expiry_or_outage() {
    for (access, status) in [
        (MockAccess::Denied, 403),
        (MockAccess::Expired, 401),
        (MockAccess::Unavailable, 503),
    ] {
        let server = ActionsServer::new().unwrap().with_access(access);
        for operation in contract().operations {
            assert_eq!(
                invoke(&server, &operation.name, sample(&operation.name))["http_status"],
                status
            );
        }
    }
}

#[test]
fn work_lifecycle_and_statistics_are_consistent() {
    let server = ActionsServer::new().unwrap();
    let created = data(&server, "createManualWork", sample("createManualWork"));
    let id = created["id"].as_i64().unwrap();
    data(
        &server,
        "assignTechnicianToWork",
        json!({"work_id":id,"technician_id":1}),
    );
    data(&server, "notifyWorkAssignment", json!({"work_id":id}));
    let updated = data(
        &server,
        "updateWork",
        json!({"work_id":id,"body":{"stato":"chiuso","note":"Completato in simulazione"}}),
    );
    assert_eq!(updated["data_chiusura"], "2026-10-15T12:00:00Z");
    assert_eq!(updated["tecnico_assegnato"]["id"], 1);
    assert_eq!(
        data(&server, "getWeeklyStats", json!({}))["closed_this_week"],
        2
    );
    for name in [
        "getClosedByOperator",
        "getClosedByTechnician",
        "getDailyClosedStats",
        "getYearlyStats",
    ] {
        let counts = data(&server, name, json!({}));
        assert_eq!(
            counts
                .as_array()
                .unwrap()
                .iter()
                .map(|row| row["closed"].as_u64().unwrap())
                .sum::<u64>(),
            2
        );
    }
    data(&server, "deleteWork", json!({"work_id":id}));
    assert_eq!(
        invoke(&server, "getWorkById", json!({"work_id":id}))["http_status"],
        404
    );
    assert_eq!(
        data(&server, "getWorks", json!({}))
            .as_array()
            .unwrap()
            .len(),
        2
    );
}

#[test]
fn equipment_lifecycle_and_conflicts() {
    let server = ActionsServer::new().unwrap();
    for (create, assign, install, get, key) in [
        (
            "createModem",
            "assignModemToWork",
            "installModem",
            "getModemById",
            "modem_id",
        ),
        (
            "createONT",
            "assignONTToWork",
            "installONT",
            "getONTById",
            "ont_id",
        ),
    ] {
        let created = data(&server, create, sample(create));
        let id = created["id"].as_i64().unwrap();
        data(&server, assign, json!({"work_id":7,key:id}));
        assert_eq!(
            invoke(&server, assign, json!({"work_id":8,key:id}))["http_status"],
            400
        );
        data(&server, install, json!({key:id}));
        assert_eq!(data(&server, get, json!({key:id}))["status"], "installato");
        assert_eq!(data(&server, get, json!({key:id}))["work_id"], 7);
    }
    data(
        &server,
        "markEquipmentDelivered",
        sample("markEquipmentDelivered"),
    );
    let equipment = data(&server, "getWorkEquipment", json!({"work_id":7}));
    assert_eq!(equipment["modem"]["id"], 2);
    assert_eq!(equipment["ont"]["id"], 2);
    assert_eq!(equipment["modem_delivered"], true);
    assert_eq!(equipment["ont_delivered"], true);
    data(&server, "deleteWork", json!({"work_id":7}));
    assert!(data(&server, "getModemById", json!({"modem_id":2}))["work_id"].is_null());
}

#[test]
fn calendar_filters_and_updates() {
    let server = ActionsServer::new().unwrap();
    let changed = data(&server, "updateAppointment", sample("updateAppointment"));
    assert_eq!(changed["changes"].as_array().unwrap().len(), 3);
    assert_eq!(
        data(
            &server,
            "getCalendar",
            json!({"from":"2026-10-16","to":"2026-10-16","tecnico_id":1})
        )["total"],
        1
    );
    assert_eq!(
        data(
            &server,
            "getCalendar",
            json!({"from":"2026-10-15","to":"2026-10-15"})
        )["total"],
        0
    );
    assert_eq!(
        data(
            &server,
            "getCalendar",
            json!({"from":"2026-10-01","to":"2026-10-31","stato":"chiuso"})
        )["total"],
        0
    );
    assert_eq!(
        invoke(
            &server,
            "getCalendar",
            json!({"from":"2026-11-01","to":"2026-10-01"})
        )["http_status"],
        400
    );
}

#[test]
fn failures_are_atomic_and_instances_are_isolated() {
    let server = ActionsServer::new().unwrap();
    let original = data(&server, "getWorks", json!({}));
    let mut body = sample("createManualWork");
    body["body"]["tecnico_assegnato"] = json!(999);
    assert_eq!(
        invoke(&server, "createManualWork", body)["http_status"],
        404
    );
    assert_eq!(data(&server, "getWorks", json!({})), original);
    assert_eq!(
        data(&server, "createManualWork", sample("createManualWork"))["id"],
        9
    );
    assert_eq!(
        invoke(&server, "createManualWork", sample("createManualWork"))["http_status"],
        400
    );
    assert_eq!(
        data(&ActionsServer::new().unwrap(), "getWorks", json!({})),
        original
    );
}

#[test]
fn validation_rejects_bad_types_dates_enums_and_large_requests() {
    let server = ActionsServer::new().unwrap();
    for (name, args) in [
        ("getWorkById", json!({"work_id":"7"})),
        (
            "updateWork",
            json!({"work_id":7,"body":{"stato":"invalido"}}),
        ),
        (
            "getCalendar",
            json!({"from":"2026-02-30","to":"2026-10-31"}),
        ),
        (
            "updateAppointment",
            json!({"work_id":7,"data_appuntamento":"domani"}),
        ),
        (
            "createModem",
            json!({"body":{"serial_number":"SIM","model":"SIM","type":"invalido"}}),
        ),
        (
            "updateWork",
            json!({"work_id":7,"body":{"note":"a".repeat(17000)}}),
        ),
    ] {
        assert!(server.invoke(name, args).is_err(), "{name}");
    }
    assert!(server.invoke("ruota_chiavi", json!({})).is_err());
    assert!(server.invoke("project_write", json!({})).is_err());
}

#[test]
fn original_helpers_share_the_actions_state() {
    let server = ActionsServer::new().unwrap();
    assert_eq!(
        data(&server, "cerca_wr", json!({"numero_wr":"103579742"}))["id"],
        "work_7"
    );
    data(
        &server,
        "updateWork",
        json!({"work_id":7,"body":{"stato":"sospeso"}}),
    );
    assert_eq!(
        data(&server, "stato_wr", json!({"numero_wr":"103579742"}))["stato"],
        "sospeso"
    );
    assert_eq!(
        data(&server, "fetch", json!({"document_id":"work_7"}))["stato"],
        "sospeso"
    );
    assert_eq!(
        data(&server, "search", json!({"query":"103579742"}))["results"][0]["stato"],
        "sospeso"
    );
    assert_eq!(
        data(&server, "search", json!({"query":"TEST-ONT-003"}))["results"][0]["id"],
        "material_3"
    );
    assert_eq!(
        data(&server, "fetch", json!({"document_id":"material_3"}))["quantita"],
        4
    );
    assert_eq!(
        data(&server, "stato_api", json!({}))["production_checked"],
        false
    );
    assert_eq!(data(&server, "riepilogo_wr", json!({}))["totale"], 2);
    data(&server, "deleteWork", json!({"work_id":7}));
    assert_eq!(
        invoke(&server, "cerca_wr", json!({"numero_wr":"103579742"}))["http_status"],
        404
    );
}
