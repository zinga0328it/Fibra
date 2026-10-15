# Lia Fibra MCP

- This project is independent of /home/aaa/fibra. Do not edit that application,
  its MCP experiment, database, services, credentials, or network configuration.
- Business profiles remain mock-only. --dev-read reads real code from this
  project only, through descriptor-relative no-follow access and an allowlist.
  It exposes project_read and preview-only project_diff, never write or shell.
- Never interpret simulated results as production data or as authorization to
  switch off the existing GPT Actions. Preserve the simulated/test_http markers.
- Use the official Rust MCP SDK, pinned in Cargo.toml and Cargo.lock:
  https://github.com/modelcontextprotocol/rust-sdk
  https://docs.rs/rmcp/3.5.1/rmcp/
- Protocol reference: https://modelcontextprotocol.io/specification
- Use cargo test --locked and cargo clippy --locked --all-targets -- -D warnings.
- The --mock profile is read-only. The --mock-actions profile permits the
  32 named Actions, including in-memory simulated writes, plus six helpers.
  Never implement generic URL, SQL, shell or key-rotation tools.
- Production integration requires a verified broker contract and confirmation
  that the local Actions schema matches the active GPT. Never guess header
  names, token exchanges, or WR lookup semantics. See MIGRATION_REPORT.md.
- Do not copy any credential from the original experiment into this repository.
- HttpTestAdapter accepts only explicit loopback IPs and fabricated test auth.
  No proxy, redirects, retries or production CLI mode. Preserve these guards.
- Run Rustfmt/Clippy with the dedicated .tools toolchain; never update shared
  production tooling. A dedicated toolchain is not an OS sandbox for untrusted code.