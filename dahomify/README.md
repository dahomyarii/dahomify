# dahomify

Simple CLI to run Dahomify code-health models on any project.  
This fork is maintained independently and is **not affiliated or co-maintained** with any other organization.

---

## Quick install (ready to paste)

Requires **Python 3.11+** and **git**.

### Windows (PowerShell)

```powershell
cd C:\path\to\your\project

# Create & activate virtual env (recommended)
python -m venv .venv
.\.venv\Scripts\activate

# Install Dahomify from GitHub
pip install --upgrade "git+https://github.com/dahomyarii/dahomify.git"

# First run
dahomify scan --path .
dahomify next
```

### Linux / macOS (bash)

```bash
cd /path/to/your/project

# Create & activate virtual env (recommended)
python -m venv .venv
source .venv/bin/activate

# Install Dahomify from GitHub
pip install --upgrade "git+https://github.com/dahomyarii/dahomify.git"

# First run
dahomify scan --path .
dahomify next
```

You can re-run:

- `dahomify status` – overall health + plan  
- `dahomify next` – next highest‑value fix  
- `dahomify show security --status open` – open security items  
- `dahomify show smells --status open` – code smells

Key docs:

- `docs/ci_plan.md` - repository CI contract plus the full `ekra.app` CI/CD and DevOps blueprint
- `docs/ekra_app_delivery_guide.md` - full `ekra.app` repo strategy, testing, deployment, operations, and ownership guide
- `SHARIKLY_COMMANDS.md` - practical frontend, backend, Docker, Dahomify, and deployment commands
- `docs/CURSOR.md` - Cursor-specific agent workflow

---

## Use with an AI coding agent

Tell your agent:

```text
Install and run Dahomify on this repo.
Run:

pip install --upgrade "git+https://github.com/dahomyarii/dahomify.git"
dahomify scan --path .
dahomify next

Your goal is to make real, deep improvements to code quality (not just silence warnings).
Follow `dahomify next` and `dahomify status` until the queue is clean.
```
