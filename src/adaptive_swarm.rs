//! Prototipo di pianificazione di nuove funzionalita per singolo utente.
//! Isolato: nessuna rete, codice generato, MCP tool, persistenza o deploy.
use std::fmt;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DraftError {
    InvalidScope,
    InvalidRequest,
    WrongScope,
    WrongState,
    InvalidArtifact,
    FailedTests,
}
impl fmt::Display for DraftError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result { write!(f, "{self:?}") }
}
impl std::error::Error for DraftError {}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DraftState {
    Requested,
    Proposed,
    AwaitingReview,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FeatureDraft {
    tenant_id: String,
    user_id: String,
    request_id: String,
    description: String,
    state: DraftState,
    artifact_sha256: Option<String>,
    tests_sha256: Option<String>,
}
fn valid_id(s: &str) -> bool {
    !s.is_empty() && s.len() <= 96
        && s.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'_' || b == b'-')
}
fn valid_sha256(s: &str) -> bool {
    s.len() == 64 && s.bytes().all(|b| b.is_ascii_hexdigit() && !b.is_ascii_uppercase())
}
impl FeatureDraft {
    /// Scope must originate from verified backend identity, not model arguments.
    pub fn requested(
        tenant_id: &str, user_id: &str, request_id: &str, description: &str
    ) -> Result<Self, DraftError> {
        if !valid_id(tenant_id) || !valid_id(user_id) || !valid_id(request_id) {
            return Err(DraftError::InvalidScope);
        }
        if description.trim().is_empty() || description.len() > 4096
            || description.chars().any(|c| c == '\0')
        {
            return Err(DraftError::InvalidRequest);
        }
        Ok(Self {
            tenant_id: tenant_id.into(), user_id: user_id.into(),
            request_id: request_id.into(), description: description.into(),
            state: DraftState::Requested, artifact_sha256: None, tests_sha256: None,
        })
    }
    pub fn state(&self) -> DraftState { self.state }
    pub fn request_id(&self) -> &str { &self.request_id }
    pub fn description(&self) -> &str { &self.description }
    pub fn scope_matches(&self, tenant_id: &str, user_id: &str) -> bool {
        self.tenant_id == tenant_id && self.user_id == user_id
    }
    fn verify_scope(&self, tenant_id: &str, user_id: &str) -> Result<(), DraftError> {
        if self.scope_matches(tenant_id, user_id) { Ok(()) }
        else { Err(DraftError::WrongScope) }
    }
    /// Records only a referenced proposal hash; no executable content enters this model.
    pub fn propose(
        &mut self, tenant_id: &str, user_id: &str, artifact_sha256: &str
    ) -> Result<(), DraftError> {
        self.verify_scope(tenant_id, user_id)?;
        if self.state != DraftState::Requested { return Err(DraftError::WrongState); }
        if !valid_sha256(artifact_sha256) { return Err(DraftError::InvalidArtifact); }
        self.artifact_sha256 = Some(artifact_sha256.into());
        self.state = DraftState::Proposed;
        Ok(())
    }
    /// Caller must be a trusted test-attestation gateway, not an agent output.
    /// It must independently verify the same artifact digest and test outcome.
    pub fn record_verified_tests(
        &mut self, tenant_id: &str, user_id: &str,
        tested_artifact_sha256: &str, passed: bool
    ) -> Result<(), DraftError> {
        self.verify_scope(tenant_id, user_id)?;
        if self.state != DraftState::Proposed { return Err(DraftError::WrongState); }
        if !valid_sha256(tested_artifact_sha256)
            || self.artifact_sha256.as_deref() != Some(tested_artifact_sha256)
        { return Err(DraftError::InvalidArtifact); }
        if !passed { return Err(DraftError::FailedTests); }
        self.tests_sha256 = Some(tested_artifact_sha256.into());
        self.state = DraftState::AwaitingReview;
        Ok(())
    }
    /// A review is NOT an approval. No API to release or approve exists.
    pub fn review_ready(&self, tenant_id: &str, user_id: &str) -> bool {
        self.scope_matches(tenant_id, user_id)
            && self.state == DraftState::AwaitingReview
            && self.artifact_sha256 == self.tests_sha256
    }
}
