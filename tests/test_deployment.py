"""Validate SSH inputs and deployment rollback without contacting a server."""

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_module(name):
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "scripts/deployment" / f"{name}.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "field,value",
    [
        ("DEPLOY_HOST", "host;echo injected"),
        ("DEPLOY_USER", "-oProxyCommand=bad"),
        ("DEPLOY_PORT", "70000"),
        ("DEPLOY_IMAGE", "ghcr.io/team/app:latest"),
    ],
)
def test_invalid_deployment_inputs_never_connect(monkeypatch, field, value):
    module = load_module("deploy")
    for key, setting in {
        "DEPLOY_HOST": "example.test",
        "DEPLOY_USER": "deploy",
        "DEPLOY_SSH_KEY": "test-key",
        "DEPLOY_KNOWN_HOSTS": "test-host-key",
        "GHCR_USER": "test",
        "GHCR_TOKEN": "test-token",
        "DEPLOY_IMAGE": "ghcr.io/team/app@sha256:" + "a" * 64,
    }.items():
        monkeypatch.setenv(key, setting)
    monkeypatch.setenv(field, value)
    run = Mock()
    monkeypatch.setattr(module.subprocess, "run", run)
    with pytest.raises(SystemExit):
        module.main()
    run.assert_not_called()


@pytest.mark.parametrize("has_previous", [True, False])
def test_unhealthy_deployment_restores_previous_or_removes_first_attempt(
    monkeypatch, tmp_path, has_previous
):
    # Locking is Linux-only; mock just the lock for this filesystem/state test.
    monkeypatch.setitem(sys.modules, "fcntl", SimpleNamespace(flock=Mock(), LOCK_EX=2))
    module = load_module("remote")
    monkeypatch.setattr(module.Path, "home", lambda: tmp_path)
    directory = tmp_path / ".local/share/tgvision"
    directory.mkdir(parents=True)
    if has_previous:
        (directory / "compose.yaml").write_text("previous compose")
        (directory / ".env").write_text("previous image")
    calls = []

    def run(command, **kwargs):
        calls.append(command)
        if "up" in command and sum("up" in c for c in calls) == 1:
            raise subprocess.CalledProcessError(1, command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(module.subprocess, "run", run)
    with pytest.raises(subprocess.CalledProcessError):
        module.deploy(
            {
                "image": "new image",
                "compose": "new compose",
                "registry_user": "test",
                "registry_token": "test-token",
            }
        )
    if has_previous:
        assert (directory / "compose.yaml").read_text() == "previous compose"
        assert (directory / ".env").read_text() == "previous image"
        assert sum("up" in c for c in calls) == 2
    else:
        assert not (directory / ".env").exists()
        assert any("down" in c for c in calls)
