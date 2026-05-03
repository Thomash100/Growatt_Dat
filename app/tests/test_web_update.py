import asyncio

from app.web_update import CommandResult, WebUpdateSettings, WebUpdater, new_update_job


def test_web_updater_reports_disabled_when_not_enabled(tmp_path):
    (tmp_path / ".git").mkdir()
    updater = WebUpdater(WebUpdateSettings(enabled=False, token=None, workdir=str(tmp_path), run_docker_compose=False))

    availability = updater.availability()

    assert availability["available"] is False
    assert "web_update_disabled" in availability["reasons"]
    assert "token_not_configured" in availability["reasons"]


def test_web_updater_runs_git_pull_steps(tmp_path):
    (tmp_path / ".git").mkdir()
    commands: list[list[str]] = []

    def runner(command, cwd, timeout_seconds):
        commands.append(command)
        assert cwd == tmp_path
        assert timeout_seconds == 30
        return CommandResult(returncode=0, output="")

    updater = WebUpdater(
        WebUpdateSettings(
            enabled=True,
            token="example-update-token-123",
            workdir=str(tmp_path),
            command_timeout_seconds=30,
            run_docker_compose=False,
        ),
        command_runner=runner,
    )
    job = asyncio.run(updater.run(new_update_job()))

    assert job.status == "succeeded"
    assert commands == [
        ["git", "status", "--porcelain"],
        ["git", "fetch", "--tags", "origin"],
        ["git", "pull", "--ff-only"],
    ]


def test_web_updater_rejects_dirty_worktree(tmp_path):
    (tmp_path / ".git").mkdir()

    def runner(command, cwd, timeout_seconds):
        if command == ["git", "status", "--porcelain"]:
            return CommandResult(returncode=0, output=" M README.md\n")
        return CommandResult(returncode=0, output="")

    updater = WebUpdater(
        WebUpdateSettings(
            enabled=True,
            token="example-update-token-123",
            workdir=str(tmp_path),
            run_docker_compose=False,
        ),
        command_runner=runner,
    )
    job = asyncio.run(updater.run(new_update_job()))

    assert job.status == "failed"
    assert job.error_status == "git_worktree_not_clean"


def test_web_updater_verifies_token():
    updater = WebUpdater(WebUpdateSettings(enabled=True, token="example-update-token-123", run_docker_compose=False))

    assert updater.verify_token("example-update-token-123") is True
    assert updater.verify_token("wrong-token") is False
    assert updater.verify_token(None) is False
