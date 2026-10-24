//! Preferenze di layout per persona. In memoria, senza persistenza o rete.
use std::collections::HashSet;

use super::{
    catalog::{self, Module},
    identity::{Actor, Scope},
};

const MAX_WIDGETS: usize = 5;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DashboardError {
    WrongOwner,
    EmptyLayout,
    TooManyModules,
    DuplicateModule,
    ForbiddenModule,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Dashboard {
    owner: Scope,
    modules: Vec<Module>,
}

impl Dashboard {
    pub fn new(owner: Scope, role: super::identity::Role) -> Self {
        Self {
            owner,
            modules: catalog::defaults(role),
        }
    }

    /// Solo il proprietario del profilo puo cambiarlo. I controlli sul DB reale
    /// devono avvenire anche nel backend, non soltanto in questo prototipo.
    pub fn set_modules(
        &mut self,
        actor: &Actor,
        requested: &[Module],
    ) -> Result<(), DashboardError> {
        if &self.owner != actor.scope() {
            return Err(DashboardError::WrongOwner);
        }
        if requested.is_empty() {
            return Err(DashboardError::EmptyLayout);
        }
        if requested.len() > MAX_WIDGETS {
            return Err(DashboardError::TooManyModules);
        }
        let mut seen = HashSet::new();
        for module in requested {
            if !seen.insert(*module) {
                return Err(DashboardError::DuplicateModule);
            }
            if !catalog::is_visible(actor.role(), *module) {
                return Err(DashboardError::ForbiddenModule);
            }
        }
        self.modules = requested.to_vec();
        Ok(())
    }

    /// Se il ruolo cambia, nasconde i moduli non piu consentiti.
    /// Le API devono applicare anche filtri su tenant, utente e WR.
    pub fn visible_modules(&self, actor: &Actor) -> Result<Vec<Module>, DashboardError> {
        if &self.owner != actor.scope() {
            return Err(DashboardError::WrongOwner);
        }
        Ok(self
            .modules
            .iter()
            .copied()
            .filter(|module| catalog::is_visible(actor.role(), *module))
            .collect())
    }

    pub fn owner(&self) -> &Scope {
        &self.owner
    }
}
