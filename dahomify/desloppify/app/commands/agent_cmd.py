"""agent command: run status, next, show, plan; write one file for Cursor/Claude to read. Optional Claude synthesis."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from desloppify.core._internal.text_utils import get_project_root
from desloppify.core.output_api import colorize


def _ensure_openai_key_from_env(root: Path) -> None:
    """Load OPENAI_API_KEY from a .env file at project root if not already set."""
    if os.environ.get("OPENAI_API_KEY"):
        return
    env_path = root / ".env"
    try:
        text = env_path.read_text(encoding="utf-8")
    except OSError:
        return
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("OPENAI_API_KEY="):
            _, val = line.split("=", 1)
            val = val.strip().strip('"').strip("'")
            if val:
                os.environ["OPENAI_API_KEY"] = val
            break


def cmd_agent(args: argparse.Namespace) -> None:
    """Gather status, next, show security/smells, plan queue into one file. Optional --scan and --synthesize."""
    root = Path(args.path).resolve() if getattr(args, "path", None) else get_project_root()
    out_file = getattr(args, "out", None)
    if out_file:
        out_path = Path(out_file).resolve()
    else:
        state_dir = root / ".desloppify"
        state_dir.mkdir(parents=True, exist_ok=True)
        out_path = state_dir / "agent_context.md"

    # Best-effort: load OPENAI_API_KEY from project .env if not set
    _ensure_openai_key_from_env(root)

    do_scan = getattr(args, "scan", False)
    do_synthesize = getattr(args, "synthesize", False)
    goal = (getattr(args, "goal", None) or "").strip()
    no_expand_goal = getattr(args, "no_expand_goal", False)
    path_str = str(root)

    def run_cmd(cmd: list[str], section_name: str) -> str:
        try:
            # No global --path; child uses cwd for get_project_root()
            # Force child to emit UTF-8 so we don't get mojibake on Windows (cp1252 console)
            # Wide width so plan queue / status tables don't truncate summaries
            env = {**os.environ, "PYTHONIOENCODING": "utf-8", "COLUMNS": "200"}
            result = subprocess.run(
                [sys.executable, "-m", "desloppify"] + cmd,
                cwd=str(root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=300,
                env=env,
            )
            out = (result.stdout or "").strip()
            err = (result.stderr or "").strip()
            if err and "Consider re-running" not in err:
                out = out + "\n\n(stderr)\n" + err if out else err
            return f"## {section_name}\n\n```\n{out}\n```\n\n" if out else f"## {section_name}\n\n(no output)\n\n"
        except subprocess.TimeoutExpired:
            return f"## {section_name}\n\n(timeout)\n\n"
        except Exception as e:
            return f"## {section_name}\n\n(error: {e})\n\n"

    parts = []
    parts.append("# Dahomify agent context\n\n")
    parts.append(f"Project root: `{path_str}`\n\n")
    parts.append("Use this file as the single source of truth for what to do next. Run tests after each change.\n\n")
    parts.append("## Before you start\n\n")
    parts.append("- **Activate the project venv**: Windows: `.venv\\Scripts\\activate` · Linux/macOS: `source .venv/bin/activate` (or the project's venv path).\n\n")
    parts.append("- **Install dependencies**: From project root run `pip install -r requirements.txt` (backend) and/or `npm install` (frontend) so the env is ready.\n\n")
    parts.append("---\n\n")
    if goal:
        parts.append("## User goal\n\n")
        parts.append(f"> {goal}\n\n")
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key and not no_expand_goal:
            print(colorize("  Expanding goal with Claude...", "dim"), file=sys.stderr)
            refined = _expand_goal(goal, api_key)
            if refined:
                parts.append("### Refined for the agent (clear, actionable steps)\n\n")
                parts.append(refined)
                parts.append("\n")
            else:
                parts.append("*(Goal expansion failed; use the raw goal above.)*\n\n")
        parts.append("Prioritize this goal when working the queue below. If the goal is a feature or fix, do it in line with the **Next 20** and **Plan queue**; run tests and refresh with `dahomify agent` after changes.\n\n")
        parts.append("---\n\n")

    if do_scan:
        print(colorize("  Running scan...", "dim"), file=sys.stderr)
        parts.append(run_cmd(["scan"], "Scan (full)"))

    print(colorize("  Running status...", "dim"), file=sys.stderr)
    parts.append(run_cmd(["status"], "Status"))
    print(colorize("  Running next...", "dim"), file=sys.stderr)
    parts.append(run_cmd(["next", "--count", "20", "--format", "terminal"], "Next 20"))
    print(colorize("  Running show security...", "dim"), file=sys.stderr)
    parts.append(run_cmd(["show", "security", "--status", "open", "--top", "50"], "Security (open)"))
    print(colorize("  Running show smells...", "dim"), file=sys.stderr)
    parts.append(run_cmd(["show", "smells", "--status", "open", "--top", "50"], "Smells (open)"))
    print(colorize("  Running plan queue...", "dim"), file=sys.stderr)
    parts.append(run_cmd(["plan", "queue", "--top", "50"], "Plan queue"))

    parts.append("*Table summaries are truncated for width; see **Next 20** above for full finding text.*\n\n")
    parts.append("---\n\n## Next steps\n\n")
    parts.append("1. **Setup**: Activate the project venv and run `pip install -r requirements.txt` (and `npm install` if frontend) so the env is ready.\n\n")
    parts.append("2. **Work the queue**: Use the **Next 20** list above, or run `dahomify next` for the single highest-priority item. If a **User goal** is set above, do that in line with the queue.\n\n")
    parts.append("3. **After each change**: Run tests, then mark done with `dahomify plan done <id> --attest \"...\"` or re-run `dahomify agent` to refresh this file.\n\n")
    parts.append("4. **Reorder or scope**: Use `dahomify plan`, `dahomify next --tier N`, or `dahomify next --cluster <name>`.\n\n")

    body = "".join(parts)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(body, encoding="utf-8")
    print(colorize(f"  Context written to: {out_path}", "green"), file=sys.stderr)

    if do_synthesize:
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            plan_path = out_path.parent / "agent_plan.md"
            _synthesize_plan(body, plan_path, api_key)
            print(colorize(f"  Plan written to: {plan_path}", "green"), file=sys.stderr)
        else:
            print(colorize("  Set OPENAI_API_KEY to use --synthesize.", "yellow"), file=sys.stderr)

    print()
    print(colorize("Tell Cursor:", "cyan"), file=sys.stderr)
    print(f"  Read {out_path} and execute the AGENT PLAN / Next items. Re-run tests and dahomify after each change.", file=sys.stderr)


def _expand_goal(goal: str, api_key: str) -> str:
    """Ask OpenAI to turn a short user goal into extremely clear, precise, actionable steps for the agent."""
    import urllib.request

    system = """You are a task specifier for a coding agent. The user gives a short goal (e.g. "dark mode", "add dark mode"). Your job is to make it EXTREMELY clear and precise so the agent has no ambiguity.

Output a short markdown document with these sections. Use the exact section headers below.

**Goal (one line)**  
One clear sentence stating the outcome (e.g. "Add a full dark/light theme with a persistent user toggle and no flash of wrong theme on load.").

**Tech / scope**  
2–4 bullets: stack (e.g. Next.js, Tailwind), approach (e.g. next-themes vs custom context, class on html vs CSS variables), and which part of the app (e.g. frontend_v2, app layout and all pages).

**Steps (precise, 6–12 items)**  
Numbered list. Each step must be concrete and actionable. For "dark mode" include:
1. Theme provider: where to add it (file path), what it does (set class or data-theme on document, read/write localStorage).
2. Tailwind: ensure darkMode is configured (e.g. darkMode: "class" in tailwind.config), and where global styles live.
3. Design tokens: use Tailwind dark: variants (e.g. bg-white dark:bg-gray-900) or CSS variables; list which surfaces to update (layout, cards, inputs, modals, header).
4. Toggle UI: where to add the switch (e.g. header/nav), what it does (toggle theme, persist to localStorage), icon (e.g. sun/moon).
5. First-load behavior: respect system preference (prefers-color-scheme) if no saved preference; avoid flash of wrong theme (script in head or provider that runs before paint).
6. Audit key pages/components: list 3–5 files or areas that must support dark styles.
7. Acceptance: how to verify (no theme flash, toggle works, preference persists, run tests).

For other goals (fixes, refactors), be equally precise: which files, what to change, how to verify. Output only this markdown. No preamble."""

    payload = {
        "model": "gpt-4.1-mini",
        "max_tokens": 1024,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": goal},
        ],
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            out = json.loads(resp.read().decode())
        choices = out.get("choices") or []
        if choices:
            message = choices[0].get("message") or {}
            content = message.get("content")
            if isinstance(content, str):
                return content.strip()
    except Exception:
        pass
    return ""


def _synthesize_plan(context: str, plan_path: Path, api_key: str) -> None:
    """Call OpenAI to produce a short execution plan; write to plan_path."""
    import urllib.request

    system = """You are a coding-agent planner. Given Dahomify status/next/security/smells/plan output, produce a single markdown document with:
1. "Summary" (2-3 sentences: scores, biggest drags, security count).
2. "Ordered execution plan" with 3-7 concrete steps. Each step: one sentence + optional dahomify/show command.
3. "Constraints": never commit secrets; run tests after each step; re-run dahomify next after fixes.
Keep it under 80 lines. Write only the markdown, no preamble."""

    payload = {
        "model": "gpt-4.1-mini",
        "max_tokens": 1024,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": context[:120000]},
        ],
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            out = json.loads(resp.read().decode())
        for block in out.get("content", []):
            if block.get("type") == "text":
                plan_path.write_text(block["text"], encoding="utf-8")
                return
    except Exception as e:
        plan_path.write_text(f"# Synthesis failed\n\n{e}\n", encoding="utf-8")
