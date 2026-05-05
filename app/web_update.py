from __future__ import annotations

import asyncio
import hmac
import os
import shutil
import subprocess
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

from app.models import datetime_to_iso, parse_bool, utc_now


CommandRunner = Callable[[list[str], Path, float], "CommandResult"]


@dataclass(frozen=True, slots=True)
class WebUpdateSettings:
    enabled: bool = False
    token: str | None = None
    token_required: bool = True
    workdir: str = "/app"
    command_timeout_seconds: float = 600.0
    require_clean_tree: bool = True
    run_docker_compose: bool = True
    restart_after_success: bool = False

    @classmethod
    def from_mapping(cls, values: dict[str, str]) -> "WebUpdateSettings":
        return cls(
            enabled=parse_bool(values.get("WEB_UPDATE_ENABLED", "false")),
            token=_empty_to_none(values.get("WEB_UPDATE_TOKEN")),
            token_required=parse_bool(values.get("WEB_UPDATE_TOKEN_REQUIRED", "true")),
            workdir=str(values.get("WEB_UPDATE_WORKDIR", "/app")).strip() or "/app",
            command_timeout_seconds=float(values.get("WEB_UPDATE_COMMAND_TIMEOUT_SECONDS", 600.0)),
            require_clean_tree=parse_bool(values.get("WEB_UPDATE_REQUIRE_CLEAN_TREE", "true")),
            run_docker_compose=parse_bool(values.get("WEB_UPDATE_RUN_DOCKER_COMPOSE", "true")),
            restart_after_success=parse_bool(values.get("WEB_UPDATE_RESTART_AFTER_SUCCESS", "false")),
        )

    def validate(self) -> None:
        if self.enabled and self.token_required and (not self.token or len(self.token) < 16):
            raise ValueError("WEB_UPDATE_TOKEN must contain at least 16 characters when web update is enabled")
        if self.command_timeout_seconds <= 0:
            raise ValueError("WEB_UPDATE_COMMAND_TIMEOUT_SECONDS must be greater than 0")

    @property
    def token_configured(self) -> bool:
        return bool(self.token)


@dataclass(frozen=True, slots=True)
class CommandResult:
    returncode: int
    output: str


@dataclass(slots=True)
class WebUpdateStep:
    name: str
    command: list[str]
    started_at: datetime
    ended_at: datetime | None = None
    returncode: int | None = None
    output: str = ""
    error_status: str | None = None

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["started_at"] = datetime_to_iso(self.started_at)
        payload["ended_at"] = None if self.ended_at is None else datetime_to_iso(self.ended_at)
        payload["command"] = " ".join(self.command)
        return payload


@dataclass(slots=True)
class WebUpdateJob:
    id: str
    status: str
    started_at: datetime
    ended_at: datetime | None = None
    steps: list[WebUpdateStep] = field(default_factory=list)
    error_status: str | None = None
    restart_requested: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "status": self.status,
            "started_at": datetime_to_iso(self.started_at),
            "ended_at": None if self.ended_at is None else datetime_to_iso(self.ended_at),
            "steps": [step.to_dict() for step in self.steps],
            "error_status": self.error_status,
            "restart_requested": self.restart_requested,
        }


class WebUpdateError(RuntimeError):
    pass


class WebUpdater:
    def __init__(
        self,
        settings: WebUpdateSettings,
        *,
        command_runner: CommandRunner | None = None,
        exit_process: Callable[[], None] | None = None,
    ) -> None:
        self.settings = settings
        self.command_runner = command_runner or run_command
        self.exit_process = exit_process or default_exit_process

    def availability(self) -> dict[str, object]:
        reasons: list[str] = []
        workdir = Path(self.settings.workdir)
        docker_command = find_docker_compose_command()

        if not self.settings.enabled:
            reasons.append("web_update_disabled")
        if self.settings.token_required and not self.settings.token_configured:
            reasons.append("token_not_configured")
        if not workdir.exists():
            reasons.append("workdir_missing")
        elif not (workdir / ".git").exists():
            reasons.append("git_repository_missing")
        if shutil.which("git") is None:
            reasons.append("git_command_missing")
        if self.settings.run_docker_compose and docker_command is None:
            reasons.append("docker_compose_missing")

        return {
            "enabled": self.settings.enabled,
            "available": not reasons,
            "reasons": reasons,
            "workdir": str(workdir),
            "token_required": self.settings.token_required,
            "run_docker_compose": self.settings.run_docker_compose,
            "restart_after_success": self.settings.restart_after_success,
            "docker_compose_command": docker_command,
        }

    def verify_token(self, token: str | None) -> bool:
        if not self.settings.token_required:
            return True
        expected = self.settings.token or ""
        provided = token or ""
        return bool(expected) and hmac.compare_digest(provided, expected)

    async def run(self, job: WebUpdateJob) -> WebUpdateJob:
        try:
            self._validate_before_run()
            if self.settings.require_clean_tree:
                await self._run_step(job, "check_worktree", ["git", "status", "--porcelain"])
                last_output = job.steps[-1].output.strip()
                if last_output:
                    raise WebUpdateError("git_worktree_not_clean")
            await self._run_step(job, "fetch", ["git", "fetch", "--tags", "origin"])
            await self._run_step(job, "pull", ["git", "pull", "--ff-only"])
            if self.settings.run_docker_compose:
                docker_command = find_docker_compose_command()
                if docker_command is None:
                    raise WebUpdateError("docker_compose_missing")
                await self._run_step(job, "docker_compose_up", [*docker_command, "up", "-d", "--build"])
            job.status = "succeeded"
            if self.settings.restart_after_success:
                job.restart_requested = True
                asyncio.create_task(self._exit_soon())
        except Exception as exc:
            job.status = "failed"
            job.error_status = str(exc)
        finally:
            job.ended_at = utc_now()
        return job

    def _validate_before_run(self) -> None:
        availability = self.availability()
        if not availability["available"]:
            reasons = ",".join(str(reason) for reason in availability["reasons"])
            raise WebUpdateError(reasons)

    async def _run_step(self, job: WebUpdateJob, name: str, command: list[str]) -> None:
        step = WebUpdateStep(name=name, command=command, started_at=utc_now())
        job.steps.append(step)
        try:
            result = await asyncio.to_thread(
                self.command_runner,
                command,
                Path(self.settings.workdir),
                self.settings.command_timeout_seconds,
            )
        except Exception as exc:
            step.ended_at = utc_now()
            step.returncode = -1
            step.error_status = str(exc)
            raise WebUpdateError(f"{name}_failed: {exc}") from exc

        step.ended_at = utc_now()
        step.returncode = result.returncode
        step.output = trim_output(result.output)
        if result.returncode != 0:
            step.error_status = f"exit_{result.returncode}"
            raise WebUpdateError(f"{name}_failed: exit_{result.returncode}")

    async def _exit_soon(self) -> None:
        await asyncio.sleep(2)
        self.exit_process()


def run_command(command: list[str], cwd: Path, timeout_seconds: float) -> CommandResult:
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )
    return CommandResult(
        returncode=completed.returncode,
        output=(completed.stdout or "") + (completed.stderr or ""),
    )


def find_docker_compose_command() -> list[str] | None:
    docker = shutil.which("docker")
    if docker:
        try:
            result = subprocess.run(
                [docker, "compose", "version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if result.returncode == 0:
                return [docker, "compose"]
        except Exception:
            pass

    docker_compose = shutil.which("docker-compose")
    if docker_compose:
        try:
            result = subprocess.run(
                [docker_compose, "version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if result.returncode == 0:
                return [docker_compose]
        except Exception:
            pass
    return None


def new_update_job() -> WebUpdateJob:
    return WebUpdateJob(id=str(uuid.uuid4()), status="running", started_at=utc_now())


def trim_output(output: str, limit: int = 12000) -> str:
    if len(output) <= limit:
        return output
    return output[-limit:]


def default_exit_process() -> None:
    os._exit(0)


def _empty_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None
