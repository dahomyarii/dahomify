## dahomify

Simple CLI to run Dahomify code‑health models on any project.  
This fork is maintained independently and is **not affiliated or co‑maintained** with any other organization.

---

### What Dahomify does

- **DevOps**: Surface infra/security issues in your repos, keep CI pipelines and config files healthy.
- **Software engineering**: Continuously improve code structure, smells, and test coverage.
- **Bug work**: Triage risky areas and suggest next high‑value places to harden or debug.

At a high level you:

1. **Scan** a repo once (or on a schedule).  
2. **Ask for the next best fix**.  
3. **Apply fixes** and repeat until the queue is clean.

---

## Installation

Requires **Python 3.11+** and **git**.

### Windows (PowerShell)

```powershell
# 1) Go to the repo you want to analyze
cd C:\path\to\your\project

# 2) (Recommended) Create & activate a virtual env
python -m venv .venv
.\.venv\Scripts\activate

# 3) Install Dahomify from GitHub
pip install --upgrade "git+https://github.com/dahomyarii/dahomify.git"

# 4) First run
dahomify scan --path .
dahomify next
```

### Linux (bash / zsh)

```bash
# 1) Go to the repo you want to analyze
cd /path/to/your/project

# 2) (Recommended) Create & activate a virtual env
python -m venv .venv
source .venv/bin/activate

# 3) Install Dahomify from GitHub
pip install --upgrade "git+https://github.com/dahomyarii/dahomify.git"

# 4) First run
dahomify scan --path .
dahomify next
```

### Global install (optional)

If you prefer a global CLI instead of per‑project virtualenvs:

```bash
pipx install "git+https://github.com/dahomyarii/dahomify.git"
```

Then you can run `dahomify` in any project (after activating the right Python version).

---

## Core commands

These are the main commands you’ll use day‑to‑day:

- **`dahomify scan --path .`**: Analyze the current repo and build a code‑health plan.
- **`dahomify status`**: Show overall health, open items, and the current improvement plan.
- **`dahomify next`**: Get the single highest‑value next action to take.
- **`dahomify show security --status open`**: List open security‑related issues.
- **`dahomify show smells --status open`**: List code‑smell items (complexity, duplication, etc.).

For full details, always refer to:

```bash
dahomify --help
dahomify <command> --help
```

---

## Usage by role / workflow

### DevOps workflow

- **Continuous repo hygiene**
  - **Initial**: `dahomify scan --path .`
  - **Daily/weekly**: `dahomify status` to see infra, config, and security‑adjacent issues.
  - **Next actions**: `dahomify next` until the queue is reasonably small.
- **Security views**
  - `dahomify show security --status open` to list security‑flavored items that need attention.
  - Work from the list and re‑run `scan` periodically as the repo evolves.

You can wire Dahomify into CI by running `dahomify scan --path .` on a schedule and failing the pipeline when certain categories cross a threshold (for that, have the pipeline call `dahomify status` and parse its output).

### Software engineering workflow

- **Improve an existing codebase**
  - Run `dahomify scan --path .` once.
  - Use `dahomify status` to understand hot spots and themes.
  - Use `dahomify next` to get a concrete, bite‑sized refactor or fix to apply.
- **Clean up over time**
  - Before starting a feature branch, run `dahomify next` and fix 1–2 items touching the area you’re about to work in.
  - Periodically run `dahomify show smells --status open` to hunt down tech‑debt in key modules.

### Bug‑focused workflow

- **When a bug appears**
  - Run `dahomify scan --path .` (or re‑use an existing scan).
  - Use `dahomify status` to see if the affected module already shows up as risky or smelly.
  - Use `dahomify next` to guide small, high‑value structural changes around the buggy area (e.g., better tests, splitting big functions).
- **After fixing**
  - Re‑run `dahomify scan --path .`.
  - Confirm with `dahomify status` that risk and smell counts in the area are trending down.

---

## Working with shortcuts (PowerShell helper)

If you want a very short command to run common Dahomify workflows on Windows, you can define a `dahomify` PowerShell helper that manages shortcuts such as:

- **`dahomify shortcut`**: Interactively create a shortcut:
  - Example: name `rb`, command `python manage.py runserver`.
- **`dahomify rb`**: Run the shortcut named `rb`.

Internally this stores mappings like:

```text
rb=python manage.py runserver
```

in a file at `$HOME\.dahomify_shortcuts.txt`. You can also store shortcuts for common Dahomify commands, for example:

- `ds=dahomify scan --path .`
- `dn=dahomify next`
- `dst=dahomify status`

This gives you a tiny “command palette” in your shell for DevOps, software, and bug‑hunting tasks.

---

## Use with an AI coding agent

Tell your agent something like:

```text
Install and run Dahomify on this repo.
Run:

pip install --upgrade "git+https://github.com/dahomyarii/dahomify.git"
dahomify scan --path .
dahomify next

Your goal is to make real, deep improvements to code quality (not just silence warnings).
Follow `dahomify next` and `dahomify status` until the queue is clean.
```

You can additionally ask the agent to:

- Prioritize **DevOps** actions (CI config, infra, security).
- Focus on **software design** improvements (smells, complexity, tests).
- Help with **bug‑driven** hardening around specific modules, guided by Dahomify’s suggestions.
