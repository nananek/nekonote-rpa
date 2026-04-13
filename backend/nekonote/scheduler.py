"""Schedule execution for nekonote scripts.

Usage::

    from nekonote import scheduler

    scheduler.add("daily", cron="0 9 * * MON-FRI", script="report.py")
    scheduler.add("hourly", cron="0 * * * *", script="check.py")
    jobs = scheduler.list()
    scheduler.remove("daily")
    scheduler.start()  # blocks, runs scheduled jobs
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


def _jobs_path() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path.home() / ".config"
    d = base / "nekonote"
    d.mkdir(parents=True, exist_ok=True)
    return d / "schedules.json"


def _load_jobs() -> dict[str, Any]:
    path = _jobs_path()
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _save_jobs(jobs: dict[str, Any]) -> None:
    _jobs_path().write_text(json.dumps(jobs, ensure_ascii=False, indent=2), encoding="utf-8")


def add(name: str, *, cron: str, script: str, variables: dict[str, str] | None = None) -> None:
    """Register a scheduled job.

    Args:
        name: Unique job name.
        cron: Cron expression (e.g. "0 9 * * MON-FRI").
        script: Path to the .py script to execute.
        variables: Optional variables to pass to the script.
    """
    jobs = _load_jobs()
    jobs[name] = {
        "cron": cron,
        "script": str(Path(script).resolve()),
        "variables": variables or {},
        "enabled": True,
    }
    _save_jobs(jobs)


def remove(name: str) -> None:
    """Remove a scheduled job."""
    jobs = _load_jobs()
    jobs.pop(name, None)
    _save_jobs(jobs)


def list() -> dict[str, Any]:
    """List all scheduled jobs."""
    return _load_jobs()


def enable(name: str) -> None:
    """Enable a job."""
    jobs = _load_jobs()
    if name in jobs:
        jobs[name]["enabled"] = True
        _save_jobs(jobs)


def disable(name: str) -> None:
    """Disable a job without removing it."""
    jobs = _load_jobs()
    if name in jobs:
        jobs[name]["enabled"] = False
        _save_jobs(jobs)


def run_job(name: str) -> str:
    """Manually run a scheduled job now. Returns the output."""
    jobs = _load_jobs()
    if name not in jobs:
        raise KeyError(f"Job '{name}' not found")
    job = jobs[name]
    cmd = [sys.executable, "-m", "nekonote.cli", "run", job["script"], "--format", "json"]
    for k, v in job.get("variables", {}).items():
        cmd += ["--var", f"{k}={v}"]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return result.stdout + result.stderr


def start() -> None:
    """Start the scheduler daemon (blocks). Requires apscheduler."""
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger

    sched = BlockingScheduler()
    jobs = _load_jobs()

    for name, job in jobs.items():
        if not job.get("enabled", True):
            continue
        trigger = CronTrigger.from_crontab(job["cron"])
        sched.add_job(
            _execute_job,
            trigger=trigger,
            args=[name, job],
            id=name,
            name=name,
        )
        print(f"Scheduled: {name} ({job['cron']}) -> {job['script']}")

    if sched.get_jobs():
        print(f"Starting scheduler with {len(sched.get_jobs())} jobs...")
        sched.start()
    else:
        print("No enabled jobs to schedule.")


def _execute_job(name: str, job: dict) -> None:
    """Execute a single job (called by APScheduler)."""
    print(f"[{name}] Running {job['script']}...")
    output = run_job(name)
    print(f"[{name}] Done. Output: {output[:200]}")
