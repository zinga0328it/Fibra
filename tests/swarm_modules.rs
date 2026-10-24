#[path = "../src/swarm/mod.rs"]
mod swarm;

use swarm::{
    catalog::Module,
    coordinator::{Mission, MissionError, Step, TaskState},
    dashboard::{Dashboard, DashboardError},
    identity::{Actor, Role, Scope},
};

#[test]
fn dashboard_is_per_user_and_role() {
    let alice = Scope::new("azienda", "alice").unwrap();
    let bob = Scope::new("azienda", "bob").unwrap();
    let alice_actor = Actor::new_from_backend(alice.clone(), Role::Technician);
    let bob_actor = Actor::new_from_backend(bob, Role::Admin);
    let mut ui = Dashboard::new(alice, Role::Technician);
    assert_eq!(ui.visible_modules(&bob_actor), Err(DashboardError::WrongOwner));
    assert_eq!(ui.set_modules(&bob_actor, &[Module::Warehouse]), Err(DashboardError::WrongOwner));
    assert_eq!(ui.set_modules(&alice_actor, &[Module::Warehouse]), Err(DashboardError::ForbiddenModule));
    ui.set_modules(&alice_actor, &[Module::Navigator, Module::MyWorks]).unwrap();
    assert_eq!(ui.visible_modules(&alice_actor).unwrap(), vec![Module::Navigator, Module::MyWorks]);
    assert_eq!(ui.set_modules(&alice_actor, &[Module::Navigator, Module::Navigator]), Err(DashboardError::DuplicateModule));
    assert_eq!(ui.visible_modules(&alice_actor).unwrap(), vec![Module::Navigator, Module::MyWorks]);
    assert_ne!(ui.owner(), &bob);
}

#[test]
fn no_cross_tenant_identity_and_invalid_ids() {
    assert!(Scope::new("tenant", "../user").is_err());
    assert_ne!(Scope::new("tenant1", "u1").unwrap(), Scope::new("tenant2", "u1").unwrap());
}

#[test]
fn mission_runs_independent_swarms_in_parallel_after_listen() {
    let scope = Scope::new("azienda", "utente").unwrap();
    let other = Scope::new("azienda", "altro").unwrap();
    let mut m = Mission::new(scope.clone(), "req_1", "Vorrei la mia dashboard").unwrap();
    assert_eq!(m.ready(&other), Err(MissionError::WrongOwner));
    assert_eq!(m.ready(&scope).unwrap(), vec![Step::Listen]);
    assert_eq!(m.start(&scope, Step::Build), Err(MissionError::DependenciesIncomplete));
    m.start(&scope, Step::Listen).unwrap();
    assert_eq!(m.task_state(&scope, Step::Listen).unwrap(), TaskState::Running);
    m.finish(&scope, Step::Listen, true).unwrap();
    assert_eq!(m.ready(&scope).unwrap(), vec![Step::Design, Step::ApiContract, Step::Security]);
    for step in [Step::Design, Step::ApiContract, Step::Security] {
        m.start(&scope, step).unwrap();
        m.finish(&scope, step, true).unwrap();
    }
    assert_eq!(m.ready(&scope).unwrap(), vec![Step::Build]);
    m.start(&scope, Step::Build).unwrap();
    m.finish(&scope, Step::Build, true).unwrap();
    m.start(&scope, Step::Tests).unwrap();
    m.finish(&scope, Step::Tests, true).unwrap();
    m.start(&scope, Step::Review).unwrap();
    m.finish(&scope, Step::Review, true).unwrap();
    assert_eq!(m.planning_complete(&scope), Ok(true));
    assert_eq!(m.start(&scope, Step::Review), Err(MissionError::InvalidTransition));
}

#[test]
fn failures_do_not_advance_mission() {
    let scope = Scope::new("azienda", "utente").unwrap();
    let mut m = Mission::new(scope.clone(), "req_2", "Modulo").unwrap();
    m.start(&scope, Step::Listen).unwrap();
    m.finish(&scope, Step::Listen, false).unwrap();
    assert!(m.ready(&scope).unwrap().is_empty());
    assert_eq!(m.planning_complete(&scope), Ok(false));
}
