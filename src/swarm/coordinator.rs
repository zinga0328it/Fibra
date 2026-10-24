//! Un piccolo orchestratore deterministico per coordinare sciami specializzati.
//! Pianifica lavoro: NON avvia agenti, non compila codice e non autorizza deploy.
use super::identity::Scope;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub enum Step {
    Listen = 0,
    Design = 1,
    ApiContract = 2,
    Security = 3,
    Build = 4,
    Tests = 5,
    Review = 6,
}

pub const STEPS: [Step; 7] = [
    Step::Listen,
    Step::Design,
    Step::ApiContract,
    Step::Security,
    Step::Build,
    Step::Tests,
    Step::Review,
];

impl Step {
    pub fn swarm_name(self) -> &'static str {
        match self {
            Self::Listen => "ascolto",
            Self::Design => "interfaccia",
            Self::ApiContract => "contratti_api",
            Self::Security => "sicurezza",
            Self::Build => "sviluppo",
            Self::Tests => "collaudo",
            Self::Review => "revisione",
        }
    }

    pub fn prerequisites(self) -> &'static [Step] {
        match self {
            Self::Listen => &[],
            Self::Design | Self::ApiContract | Self::Security => &[Self::Listen],
            Self::Build => &[Self::Design, Self::ApiContract, Self::Security],
            Self::Tests => &[Self::Build],
            Self::Review => &[Self::Tests],
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TaskState {
    Queued,
    Running,
    Completed,
    Failed,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum MissionError {
    InvalidRequest,
    WrongOwner,
    DependenciesIncomplete,
    InvalidTransition,
}

#[derive(Debug, Clone)]
pub struct Mission {
    owner: Scope,
    request_id: String,
    description: String,
    states: [TaskState; 7],
}

impl Mission {
    pub fn new(owner: Scope, request_id: &str, description: &str) -> Result<Self, MissionError> {
        if request_id.is_empty()
            || request_id.len() > 96
            || !request_id
                .bytes()
                .all(|byte| byte.is_ascii_alphanumeric() || byte == b'_' || byte == b'-')
            || description.trim().is_empty()
            || description.len() > 4096
            || description.contains('\0')
        {
            return Err(MissionError::InvalidRequest);
        }
        Ok(Self {
            owner,
            request_id: request_id.to_string(),
            description: description.to_string(),
            states: [TaskState::Queued; 7],
        })
    }

    pub fn request_id(&self) -> &str {
        &self.request_id
    }

    pub fn description(&self) -> &str {
        &self.description
    }

    pub fn task_state(&self, actor: &Scope, step: Step) -> Result<TaskState, MissionError> {
        self.check_owner(actor)?;
        Ok(self.states[step as usize])
    }

    /// Restituisce i lavori che si possono avviare anche in parallelo.
    pub fn ready(&self, actor: &Scope) -> Result<Vec<Step>, MissionError> {
        self.check_owner(actor)?;
        Ok(STEPS
            .iter()
            .copied()
            .filter(|step| {
                self.states[*step as usize] == TaskState::Queued
                    && step
                        .prerequisites()
                        .iter()
                        .all(|dependency| self.states[*dependency as usize] == TaskState::Completed)
            })
            .collect())
    }

    pub fn start(&mut self, actor: &Scope, step: Step) -> Result<(), MissionError> {
        self.check_owner(actor)?;
        if self.states[step as usize] != TaskState::Queued {
            return Err(MissionError::InvalidTransition);
        }
        if !step
            .prerequisites()
            .iter()
            .all(|dependency| self.states[*dependency as usize] == TaskState::Completed)
        {
            return Err(MissionError::DependenciesIncomplete);
        }
        self.states[step as usize] = TaskState::Running;
        Ok(())
    }

    /// Stato informativo. La veridicita dei test deve essere verificata
    /// da un runner indipendente prima di qualsiasi approvazione.
    pub fn finish(
        &mut self,
        actor: &Scope,
        step: Step,
        succeeded: bool,
    ) -> Result<(), MissionError> {
        self.check_owner(actor)?;
        if self.states[step as usize] != TaskState::Running {
            return Err(MissionError::InvalidTransition);
        }
        self.states[step as usize] = if succeeded {
            TaskState::Completed
        } else {
            TaskState::Failed
        };
        Ok(())
    }

    /// Questa funzione indica SOLO che la pianificazione e conclusa.
    /// Non equivale a test certificati, approvazione umana o rilascio.
    pub fn planning_complete(&self, actor: &Scope) -> Result<bool, MissionError> {
        self.check_owner(actor)?;
        Ok(self.states.iter().all(|state| *state == TaskState::Completed))
    }

    fn check_owner(&self, actor: &Scope) -> Result<(), MissionError> {
        if &self.owner == actor {
            Ok(())
        } else {
            Err(MissionError::WrongOwner)
        }
    }
}
