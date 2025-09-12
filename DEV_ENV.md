Developer environment checklist

1) Use the project virtualenv
   - PowerShell: & .\.venv\Scripts\Activate.ps1
   - cmd: .\.venv\Scripts\activate.bat
   - bash: source .venv/bin/activate

2) Prefer MCP-managed execution
   - Use MCP servers configured in `mcp-servers.json` and VS Code settings.
   - Create tasks using `scripts/mcp_task_manager.py add "Title" "Desc"` and run via MCP.

3) Quick health checks
   - python scripts/ensure_env.py  # validates venv, packages, uvx
   - python scripts/check_mcp_imports.py  # writes scripts/check_mcp_imports.log

4) If you see repeated "python -m ..." failures:
   - Don't run ad-hoc inline python blocks in terminal. Always run scripts from files.
   - Ensure virtualenv is active before running.

5) Contact: repo maintainer
   - Add more steps here as project standardizes.

Additional project constraints

- All local paths and project root must be: `C:\dev\python-email`.
- Do NOT store or run the project from OneDrive or other synced directories.

Pinned packages (known-good for this repo)

If you encounter pydantic/pydantic-core import errors (missing symbols), run:

```powershell
pip install --force-reinstall "pydantic==2.11.7" "pydantic-core==2.33.2"
```

Recreate virtualenv and install pinned dependencies (Windows PowerShell)

```powershell
# from project root (C:\dev\python-email)
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt -c constraints.txt
```

If you want me to recreate the .venv and install dependencies, tell me and I'll run those steps.
