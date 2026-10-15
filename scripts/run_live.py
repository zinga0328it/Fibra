import os
from pathlib import Path

from dotenv import dotenv_values


def main():
    key = dotenv_values("/home/aaa/fibra/.env", interpolate=False).get("API_GPTS")
    if not key:
        raise SystemExit("Credenziale API_GPTS locale assente")
    environment = os.environ.copy()
    environment["FTTH_API_KEY"] = key
    binary = str(Path(__file__).resolve().parents[1] / ".tools/runtime/ftth-lia-mcp")
    os.execve(binary, [binary, "--live", "--http", "127.0.0.1:16033"], environment)


if __name__ == "__main__":
    main()