//! Identita e confini di tenant/utente per il prototipo.
//! ATTENZIONE: questo modulo valida soltanto i formati degli ID.
//! L'autenticazione reale e la mappatura dei ruoli spettano al backend.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Role {
    Technician,
    Logistics,
    Manager,
    Admin,
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct Scope {
    tenant_id: String,
    user_id: String,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum IdentityError {
    InvalidId,
}

impl Scope {
    pub fn new(tenant_id: &str, user_id: &str) -> Result<Self, IdentityError> {
        if !valid_id(tenant_id) || !valid_id(user_id) {
            return Err(IdentityError::InvalidId);
        }
        Ok(Self {
            tenant_id: tenant_id.to_owned(),
            user_id: user_id.to_owned(),
        })
    }

    pub fn tenant_id(&self) -> &str {
        &self.tenant_id
    }

    pub fn user_id(&self) -> &str {
        &self.user_id
    }
}

fn valid_id(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 96
        && value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || byte == b'_' || byte == b'-')
}

/// Creare Actor SOLTANTO dopo autenticazione e autorizzazione lato server.
/// Non costruirlo da un role o user_id fornito dall'agente o dal browser.
#[derive(Debug, Clone)]
pub struct Actor {
    scope: Scope,
    role: Role,
}

impl Actor {
    pub fn new_from_backend(scope: Scope, role: Role) -> Self {
        Self { scope, role }
    }

    pub fn scope(&self) -> &Scope {
        &self.scope
    }

    pub fn role(&self) -> Role {
        self.role
    }
}
