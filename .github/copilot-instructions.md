# Lia Fibra MCP

- This project is independent of /home/aaa/fibra. Do not edit that application,
  its MCP experiment, database, services, credentials, or network configuration.
- The current executable is mock-only. Never interpret simulated results as
  production data or as authorization to switch off the existing GPT Actions.
- Keep the mock marker in every successful tool result and application error.
- Use the official Rust MCP SDK, pinned in Cargo.toml and Cargo.lock:
  https://github.com/modelcontextprotocol/rust-sdk
  https://docs.rs/rmcp/3.5.1/rmcp/
- Protocol reference: https://modelcontextprotocol.io/specification
- Use cargo test --locked and cargo clippy --locked --all-targets -- -D warnings.
- Only explicit read capabilities are permitted in the first release. Never
  implement a generic URL, SQL, shell, write, or key-rotation tool.
- Production integration requires the verified broker contract and GPT Actions
  schema. Never guess header names, token exchanges, or WR lookup semantics.
- Do not copy any credential from the original experiment into this repository.