use rmcp::{
    ErrorData, Json, ServerHandler, handler::server::wrapper::Parameters, schemars, tool,
    tool_handler, tool_router,
};
use rustix::fs::{FileType, Mode, OFlags};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::{fs::File, io::Read, path::Path, sync::Arc};

const LIMIT: usize = 128 * 1024;

#[derive(Deserialize, schemars::JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct ReadInput {
    pub path: String,
}

#[derive(Deserialize, schemars::JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct DiffInput {
    pub path: String,
    pub expected_sha256: String,
    pub proposed_content: String,
}

#[derive(Serialize, schemars::JsonSchema)]
pub struct ReadOutput {
    pub path: String,
    pub sha256: String,
    pub content: String,
    pub read_only: bool,
}

#[derive(Serialize, schemars::JsonSchema)]
pub struct DiffOutput {
    pub path: String,
    pub sha256: String,
    pub diff: String,
    pub read_only: bool,
}

#[derive(Clone)]
pub struct ProjectServer {
    root: Arc<File>,
}

impl ProjectServer {
    pub fn open(root: &Path) -> Result<Self, std::io::Error> {
        let descriptor = rustix::fs::open(
            root,
            OFlags::RDONLY | OFlags::DIRECTORY | OFlags::NOFOLLOW | OFlags::CLOEXEC,
            Mode::empty(),
        )?;
        Ok(Self {
            root: Arc::new(File::from(descriptor)),
        })
    }

    pub fn read(&self, path: &str) -> Result<ReadOutput, ErrorData> {
        if !allowed(path) {
            return Err(rejected("path_not_allowed"));
        }
        let mut parent = self.root.try_clone().map_err(|_| rejected("read_failed"))?;
        let components: Vec<_> = path.split('/').collect();
        for component in &components[..components.len() - 1] {
            let descriptor = rustix::fs::openat(
                &parent,
                *component,
                OFlags::RDONLY | OFlags::DIRECTORY | OFlags::NOFOLLOW | OFlags::CLOEXEC,
                Mode::empty(),
            )
            .map_err(|_| rejected("unsafe_or_missing_path"))?;
            parent = File::from(descriptor);
        }
        let descriptor = rustix::fs::openat(
            &parent,
            *components.last().unwrap(),
            OFlags::RDONLY | OFlags::NOFOLLOW | OFlags::NONBLOCK | OFlags::CLOEXEC,
            Mode::empty(),
        )
        .map_err(|_| rejected("unsafe_or_missing_path"))?;
        let metadata = rustix::fs::fstat(&descriptor).map_err(|_| rejected("read_failed"))?;
        if FileType::from_raw_mode(metadata.st_mode) != FileType::RegularFile
            || metadata.st_nlink != 1
        {
            return Err(rejected("single_link_regular_file_required"));
        }
        let mut bytes = Vec::new();
        File::from(descriptor)
            .take((LIMIT + 1) as u64)
            .read_to_end(&mut bytes)
            .map_err(|_| rejected("read_failed"))?;
        if bytes.len() > LIMIT {
            return Err(rejected("file_too_large"));
        }
        if bytes.contains(&0) {
            return Err(rejected("binary_file_refused"));
        }
        let content = String::from_utf8(bytes).map_err(|_| rejected("utf8_required"))?;
        let sha256 = format!("{:x}", Sha256::digest(content.as_bytes()));
        Ok(ReadOutput {
            path: path.into(),
            sha256,
            content,
            read_only: true,
        })
    }

    pub fn diff(&self, input: DiffInput) -> Result<DiffOutput, ErrorData> {
        if input.proposed_content.len() > LIMIT || input.proposed_content.contains('\0') {
            return Err(rejected("invalid_proposed_content"));
        }
        let current = self.read(&input.path)?;
        if current.sha256 != input.expected_sha256 {
            return Err(rejected("stale_content_hash"));
        }
        let diff = similar::TextDiff::configure()
            .timeout(std::time::Duration::from_millis(200))
            .diff_lines(&current.content, &input.proposed_content)
            .unified_diff()
            .header(&format!("a/{}", input.path), &format!("b/{}", input.path))
            .to_string();
        if diff.len() > LIMIT {
            return Err(rejected("diff_too_large"));
        }
        Ok(DiffOutput {
            path: input.path,
            sha256: current.sha256,
            diff,
            read_only: true,
        })
    }
}

fn allowed(path: &str) -> bool {
    if path.len() > 240 || path.is_empty() {
        return false;
    }
    let components: Vec<_> = path.split('/').collect();
    if components.iter().any(|component| {
        component.is_empty()
            || component.starts_with('.')
            || !component
                .bytes()
                .all(|byte| byte.is_ascii_alphanumeric() || b"._-".contains(&byte))
            || ["secret", "credential", "password", "token"]
                .iter()
                .any(|term| component.to_ascii_lowercase().contains(term))
    }) {
        return false;
    }
    match components.as_slice() {
        [
            "Cargo.toml"
            | "Cargo.lock"
            | "README.md"
            | "DEVELOPMENT_PLAN.md"
            | "MIGRATION_REPORT.md",
        ] => true,
        ["contracts", "actions.json"] => true,
        ["src" | "tests", ..] => path.ends_with(".rs"),
        ["scripts", ..] => path.ends_with(".py"),
        _ => false,
    }
}

fn rejected(code: &str) -> ErrorData {
    ErrorData::invalid_params(code.to_owned(), None)
}

#[tool_router]
impl ProjectServer {
    #[tool(
        description = "Legge soltanto file autorizzati del progetto MCP di sviluppo; non accede al gestionale.",
        annotations(
            read_only_hint = true,
            destructive_hint = false,
            idempotent_hint = true,
            open_world_hint = false
        )
    )]
    fn project_read(
        &self,
        Parameters(input): Parameters<ReadInput>,
    ) -> Result<Json<ReadOutput>, ErrorData> {
        self.read(&input.path).map(Json)
    }

    #[tool(
        description = "Anteprima diff fra file corrente e contenuto proposto, vincolata a SHA-256. Non modifica file e non esegue git.",
        annotations(
            read_only_hint = true,
            destructive_hint = false,
            idempotent_hint = true,
            open_world_hint = false
        )
    )]
    fn project_diff(
        &self,
        Parameters(input): Parameters<DiffInput>,
    ) -> Result<Json<DiffOutput>, ErrorData> {
        self.diff(input).map(Json)
    }
}

#[tool_handler(
    name = "lia-mcp-development-read",
    version = "0.1.0",
    instructions = "Legge codice reale del solo progetto MCP. Diff solo in anteprima. Nessun accesso alle API o alla produzione; scrittura, shell, test e commit non disponibili."
)]
impl ServerHandler for ProjectServer {}
