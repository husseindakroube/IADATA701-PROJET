'Déploiement sur serveur Linux, exécuté par deploy.py via SSH avec CONFIG injecté.'

import fcntl
import os
import subprocess
import tempfile
from pathlib import Path


def deploy(config: dict) -> None:
    'Télécharge avant remplacement, attend un état sain et restaure la configuration précédente en cas d’échec.'
    directory = Path.home() / ".local/share/tgvision"
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "deploy.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        compose = directory / "compose.yaml"
        env_file = directory / ".env"
        previous_compose = compose.read_text() if compose.exists() else None
        previous_env = env_file.read_text() if env_file.exists() else None
        with tempfile.TemporaryDirectory(prefix="tgvision-registry-") as credentials:
            env = {**os.environ, "DOCKER_CONFIG": credentials}
            subprocess.run(
                [
                    "docker",
                    "login",
                    "ghcr.io",
                    "--username",
                    config["registry_user"],
                    "--password-stdin",
                ],
                input=config["registry_token"],
                text=True,
                check=True,
                env=env,
            )
            subprocess.run(["docker", "pull", config["image"]], check=True, env=env)
            compose.write_text(config["compose"], encoding="utf-8")
            env_file.write_text(f"TGVISION_IMAGE={config['image']}\n", encoding="utf-8")
            command = [
                "docker",
                "compose",
                "--project-directory",
                str(directory),
                "--env-file",
                str(env_file),
                "-f",
                str(compose),
            ]
            try:
                subprocess.run(
                    command + ["up", "-d", "--wait", "--wait-timeout", "120"],
                    check=True,
                    env=env,
                )
            except subprocess.CalledProcessError:
                subprocess.run(command + ["logs", "--tail", "80"], check=False, env=env)
                if previous_compose is not None and previous_env is not None:
                    print(
                        'Échec du déploiement ; restauration de la configuration précédente.',
                        flush=True,
                    )
                    compose.write_text(previous_compose, encoding="utf-8")
                    env_file.write_text(previous_env, encoding="utf-8")
                    subprocess.run(
                        command + ["up", "-d", "--wait", "--wait-timeout", "120"],
                        check=True,
                        env=env,
                    )
                else:
                    subprocess.run(command + ["down"], check=False, env=env)
                    env_file.unlink(missing_ok=True)
                    compose.unlink(missing_ok=True)
                raise
            if previous_compose is not None and previous_env is not None:
                (directory / "compose.previous.yaml").write_text(
                    previous_compose, encoding="utf-8"
                )
                (directory / ".env.previous").write_text(previous_env, encoding="utf-8")
            print('Déploiement opérationnel : ' + config["image"], flush=True)


if __name__ == "__main__":
    if "CONFIG" not in globals():
        raise SystemExit('Exécutez deploy.py ; ce fichier nécessite les données de déploiement SSH.')
    deploy(globals()["CONFIG"])
