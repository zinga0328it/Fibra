//! Catalogo chiuso dei moduli visibili nella UI.
//! I filtri qui NON sostituiscono controlli API/DB per ogni oggetto.
use super::identity::Role;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Module {
    MyWorks,
    Calendar,
    Navigator,
    Warehouse,
    Reports,
}

pub const MODULES: [Module; 5] = [
    Module::MyWorks,
    Module::Calendar,
    Module::Navigator,
    Module::Warehouse,
    Module::Reports,
];

pub fn is_visible(role: Role, module: Module) -> bool {
    match module {
        Module::MyWorks | Module::Navigator => {
            matches!(role, Role::Technician | Role::Manager | Role::Admin)
        }
        Module::Calendar => true,
        Module::Warehouse => matches!(role, Role::Logistics | Role::Manager | Role::Admin),
        Module::Reports => matches!(role, Role::Manager | Role::Admin),
    }
}

pub fn available(role: Role) -> Vec<Module> {
    MODULES
        .iter()
        .copied()
        .filter(|module| is_visible(role, *module))
        .collect()
}

pub fn defaults(role: Role) -> Vec<Module> {
    match role {
        Role::Technician => vec![Module::MyWorks, Module::Calendar, Module::Navigator],
        Role::Logistics => vec![Module::Calendar, Module::Warehouse],
        Role::Manager => vec![Module::Calendar, Module::MyWorks, Module::Reports],
        Role::Admin => vec![Module::MyWorks, Module::Calendar, Module::Warehouse, Module::Reports],
    }
}
