"""Send a deployment payload via SSH stdin; never interpolate secrets into commands."""

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    """Deploy only when all required environment values have been supplied."""
    required = [
        "DEPLOY_HOST",
        "DEPLOY_USER",
        "DEPLOY_SSH_KEY",
        "DEPLOY_KNOWN_HOSTS",
        "DEPLOY_IMAGE",
        "GHCR_USER",
        "GHCR_TOKEN",
    ]
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise SystemExit("Missing deployment secrets/settings: " + ", ".join(missing))
    host, user = os.environ["DEPLOY_HOST"], os.environ["DEPLOY_USER"]
    port = os.environ.get("DEPLOY_PORT") or "22"
    image = os.environ["DEPLOY_IMAGE"]
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.-]*", host):
        raise SystemExit("DEPLOY_HOST must be a hostname or IPv4 address")
    if not re.fullmatch(r"[a-z_][a-z0-9_-]*", user):
        raise SystemExit("Invalid SSH user")
    if not port.isdecimal() or not 1 <= int(port) <= 65535:
        raise SystemExit("Invalid SSH port")
    if not re.fullmatch(r"ghcr\.io/[a-z0-9_./-]+@sha256:[a-f0-9]{64}", image):
        raise SystemExit("An immutable GHCR digest is required")
    payload = {
        "image": image,
        "registry_user": os.environ["GHCR_USER"],
        "registry_token": os.environ["GHCR_TOKEN"],
        "compose": (ROOT / "compose.yaml").read_text(encoding="utf-8"),
    }
    remote_source = (ROOT / "scripts/deployment/remote.py").read_text(encoding="utf-8")
    # repr encodes data as a Python string literal, not executable shell text.
    source = "import json\nCONFIG = json.loads(" + repr(json.dumps(payload)) + ")\n"
    source += remote_source
    with tempfile.TemporaryDirectory(prefix="tgvision-ssh-") as directory:
        key = Path(directory) / "id"
        known = Path(directory) / "known_hosts"
        key.write_text(os.environ["DEPLOY_SSH_KEY"].strip() + "\n", encoding="utf-8")
        key.chmod(0o600)
        known.write_text(
            os.environ["DEPLOY_KNOWN_HOSTS"].strip() + "\n", encoding="utf-8"
        )
        command = [
            "ssh",
            "-i",
            str(key),
            "-p",
            port,
            "-o",
            "BatchMode=yes",
            "-o",
            "IdentitiesOnly=yes",
            "-o",
            "StrictHostKeyChecking=yes",
            "-o",
            f"UserKnownHostsFile={known}",
            "-o",
            "ConnectTimeout=15",
            f"{user}@{host}",
            "python3 -",
        ]
        result = subprocess.run(command, input=source, text=True, check=False)
        if result.returncode:
            raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
