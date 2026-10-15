# Lia Fibra MCP

- GitHub destination authorized by the user: zinga0328it/Fibra, branch aaa-mcp.
  This is the standalone Rust MCP tree/history, not a merge into the backend.
  The backend on AAA uses main in its separate local checkout. Other branches
  belong to other PCs: never modify/delete them. Push only to the explicit
  aaa-mcp destination; never force, mirror or push --all.
- Before changing this integration, read the current section of
  /home/aaa/fibra/obsidian/MCP-Lia-Fibra/STATO-E-DIARIO.md and MIGRATION_REPORT.md.
  Current verified status supersedes historical entries. Do not ask again for
  documented architecture or decisions; verify only volatile facts needed for
  the task. Update the diary after significant changes, including test results,
  deployment status and remaining limitations. MCP/ in the Fibra repository is
  the legacy experiment, not this active Rust server.
- This project is independent of /home/aaa/fibra. Exception explicitly approved
  on 2026-10-16: targeted persistence fixes to app/schemas.py, app/routes/works.py
  and manual.py, tests/test_app.py regressions, API-only ftth.service restart
  after backup and isolated tests. No other changes to the original app,
  MCP experiment, database, credentials or network.
- On 2026-10-16 the user explicitly requested all API operations, including writes.
  --live enables all 32 Actions and six helpers; --live-read-only remains optional.
  Use only the fixed verified ingress
  https://servicess.net/gestionale-gpt/, client credential in FTTH_API_KEY only.
  Never acquire relay/internal keys in the client. Only the approved API restart
  is allowed; do not restart bot, tunnel or unrelated services.
  Do not perform real test writes without an explicit operation/target requested
  by the user. Test mutations with synthetic loopback servers. Keep zero retries;
  unknown write outcomes require reconciliation, never blind resubmission.
  --dev-read reads real code from this
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
- The provided ALEX config separates human /gestionale/ (IP allowlist) from
  /gestionale-gpt/ (broker). ALEX injects X-Relay-Key; ZINGA injects X-Internal-Key.
  Never infer active routing from older hardening proposals. Do not alter GPT
  Actions or enable writes based on health alone; explicit authorization and
  adapter tests were obtained. WR helpers use verified GET /works/ and exact
  string matching, preserve leading zeros and reject duplicates. Collection
  reads are documented and limited to 16 MiB. Equipment IDs are ont_ID/modem_ID.
  See MIGRATION_REPORT.md and the authorized Obsidian MCP diary on AAA.
- Do not copy any credential from the original experiment into this repository.
- HttpTestAdapter accepts only explicit loopback IPs and fabricated test auth.
  No proxy, redirects or retries; never expose its destination in a CLI argument.
  Keep live startup fail-closed on health failure, with no simulated fallback.
  Normalize only the verified legacy UTC health timestamp. Validate other ISO
  datetimes without inventing a timezone. src/live_contract.rs reflects verified
  API differences; keep the original contracts/actions.json unchanged.
  Approved backend fixes persist extra_fields/telefono_cliente/modem_sn/
  note_chiusura and manual notes. MCP supports these fields; keep metadata
  nested and reject conflicting technician aliases. Four isolated API tests
  cover these fixes; never use the production DB for tests.
- Run Rustfmt/Clippy with the dedicated .tools toolchain; never update shared
  production tooling. A dedicated toolchain is not an OS sandbox for untrusted code.