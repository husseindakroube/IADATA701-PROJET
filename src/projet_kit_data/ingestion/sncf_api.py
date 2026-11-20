"""Récupérer et enregistrer les données brutes mensuelles de régularité TGV SNCF."""

from __future__ import annotations

import json
import os
import tempfile
import time
from collections.abc import Sequence
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, TypeGuard

import requests

SNCF_EXPORT_URL = (
    "https://ressources.data.sncf.com/api/explore/v2.1/catalog/datasets/"
    "regularite-mensuelle-tgv-aqst/exports/json"
)
DEFAULT_RAW_DATA_PATH = Path("data/raw/regularite-mensuelle-tgv-aqst.json")
_RETRYABLE_STATUS_CODES = {429, *range(500, 600)}


class SNCFAPIError(RuntimeError):
    """Représenter un échec HTTP ou de structure de réponse de l’API SNCF.

    :param message: Description de l’échec de l’API.
    :type message: str
    """

    def __init__(self, message: str) -> None:
        """Initialiser l’erreur d’API avec un message descriptif.

        :param message: Description de l’échec de l’API.
        :type message: str
        :returns: Aucune valeur.
        :rtype: None
        """
        super().__init__(message)


def _is_record_array(value: Any) -> TypeGuard[list[dict[str, Any]]]:
    """Indiquer si *value* est un tableau JSON ne contenant que des objets."""
    return isinstance(value, list) and all(isinstance(record, dict) for record in value)


def _retry_after_seconds(value: str | None) -> float | None:
    """Convertir la valeur HTTP Retry-After en délai positif ou nul."""
    if value is None:
        return None

    try:
        return max(0.0, float(value))
    except ValueError:
        try:
            retry_at = parsedate_to_datetime(value)
        except (TypeError, ValueError, OverflowError):
            return None

        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=UTC)
        return max(0.0, (retry_at - datetime.now(UTC)).total_seconds())


def _wait_before_retry(
    retry_number: int,
    backoff_factor: float,
    retry_after: str | None = None,
) -> None:
    """Attendre selon un backoff exponentiel en respectant Retry-After si valide."""
    backoff = backoff_factor * (2**retry_number)
    retry_after_delay = _retry_after_seconds(retry_after)
    time.sleep(max(backoff, retry_after_delay or 0.0))


def fetch_raw_data(
    *,
    connect_timeout: float = 5.0,
    read_timeout: float = 60.0,
    max_retries: int = 3,
    backoff_factor: float = 1.0,
) -> list[dict[str, Any]]:
    """Récupérer toutes les données de régularité TGV SNCF sans les transformer.

    La fonction appelle le point de terminaison d’export JSON de l’API Explore
    SNCF v2.1 avec ``limit=-1``. Les erreurs de connexion temporaires, les
    délais d’attente dépassés, les réponses HTTP 429 et les réponses HTTP 5xx
    font l’objet d’un maximum de ``max_retries`` nouvelles tentatives.

    :param connect_timeout: Durée maximale, en secondes, d’établissement de la
        connexion.
    :type connect_timeout: float
    :param read_timeout: Durée maximale, en secondes, d’attente des données de
        réponse.
    :type read_timeout: float
    :param max_retries: Nombre de nouvelles tentatives après la requête initiale.
    :type max_retries: int
    :param backoff_factor: Délai de base, en secondes, du backoff exponentiel.
    :type backoff_factor: float
    :returns: Les enregistrements sous forme de liste de dictionnaires, avec
        conservation des noms de champs et valeurs de la réponse JSON.
    :rtype: list[dict[str, Any]]
    :raises SNCFAPIError: Si la requête échoue après les nouvelles tentatives,
        si le serveur renvoie un statut d’échec non réessayable ou si la
        structure JSON n’est pas un tableau d’objets.
    :raises requests.exceptions.JSONDecodeError: Si le corps de la réponse ne
        contient pas de JSON valide. Cette exception est propagée telle quelle.
    :raises ValueError: Si un délai d’attente, le nombre de tentatives ou le
        facteur de backoff est négatif ou autrement invalide.
    """
    if connect_timeout <= 0 or read_timeout <= 0:
        raise ValueError("Les délais d’attente doivent être strictement positifs.")
    if max_retries < 0:
        raise ValueError("max_retries doit être positif ou nul.")
    if backoff_factor < 0:
        raise ValueError("backoff_factor doit être positif ou nul.")

    timeout = (connect_timeout, read_timeout)
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(
                SNCF_EXPORT_URL,
                params={"limit": -1},
                timeout=timeout,
            )
        except (requests.ConnectionError, requests.Timeout) as exc:
            if attempt < max_retries:
                _wait_before_retry(attempt, backoff_factor)
                continue
            raise SNCFAPIError(
                f"La requête à l’API SNCF a échoué après {max_retries} nouvelles tentatives : {exc}"
            ) from exc
        except requests.RequestException as exc:
            raise SNCFAPIError(f"La requête à l’API SNCF a échoué : {exc}") from exc

        if response.status_code in _RETRYABLE_STATUS_CODES:
            if attempt < max_retries:
                _wait_before_retry(
                    attempt,
                    backoff_factor,
                    response.headers.get("Retry-After"),
                )
                continue
            try:
                response.raise_for_status()
            except requests.HTTPError as exc:
                raise SNCFAPIError(
                    f"L’API SNCF a renvoyé le statut HTTP {response.status_code} après "
                    f"{max_retries} nouvelles tentatives."
                ) from exc
            raise SNCFAPIError(
                f"L’API SNCF a renvoyé le statut HTTP {response.status_code}, réessayable, "
                f"après {max_retries} nouvelles tentatives."
            )

        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise SNCFAPIError(
                f"L’API SNCF a renvoyé le statut HTTP {response.status_code} : {exc}"
            ) from exc

        records = response.json()
        if not _is_record_array(records):
            raise SNCFAPIError(
                "Réponse inattendue de l’API SNCF : un tableau JSON ne contenant "
                "que des objets était attendu."
            )
        return records

    raise SNCFAPIError("La requête à l’API SNCF a échoué sans réponse.")


def save_raw_data(
    records: Sequence[dict[str, Any]],
    path: str | os.PathLike[str] = DEFAULT_RAW_DATA_PATH,
) -> Path:
    """Enregistrer atomiquement les données brutes dans un tableau JSON UTF-8.

    Les répertoires parents sont créés si nécessaire. Un fichier temporaire
    placé dans le répertoire cible est remplacé à l’aide de :func:`os.replace`,
    afin que les lecteurs ne voient jamais une sortie partiellement écrite.

    :param records: Dictionnaires des données brutes à sérialiser sans ETL ni
        nettoyage.
    :type records: Sequence[dict[str, Any]]
    :param path: Chemin du fichier de destination. Par défaut, chemin des
        données brutes du projet.
    :type path: str | os.PathLike[str]
    :returns: Chemin de destination.
    :rtype: pathlib.Path
    :raises OSError: Si la création des répertoires, l’écriture du fichier
        temporaire ou le remplacement de la destination échoue. Le fichier
        temporaire est supprimé si possible avant de relancer l’erreur.
    :raises TypeError: Si un enregistrement contient une valeur qui ne peut
        pas être encodée en JSON.
    """
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None

    try:
        file_descriptor, temporary_name = tempfile.mkstemp(
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as output_file:
            json.dump(records, output_file, ensure_ascii=False, indent=2)
            output_file.write("\n")
            output_file.flush()
            os.fsync(output_file.fileno())
        os.replace(temporary_path, destination)
    except BaseException:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
        raise

    return destination


def load_raw_data(
    path: str | os.PathLike[str] = DEFAULT_RAW_DATA_PATH,
) -> list[dict[str, Any]]:
    """Charger un tableau JSON brut SNCF précédemment enregistré.

    :param path: Chemin du fichier JSON. Par défaut, chemin des données brutes
        du projet.
    :type path: str | os.PathLike[str]
    :returns: Dictionnaires décodés des enregistrements, avec leurs noms de
        champs et valeurs d’origine.
    :rtype: list[dict[str, Any]]
    :raises OSError: Si le fichier ne peut pas être ouvert ou lu. Cette
        exception inclut :class:`FileNotFoundError` si le chemin n’existe pas.
    :raises json.JSONDecodeError: Si le fichier ne contient pas de JSON valide.
    :raises ValueError: Si le JSON décodé n’est pas un tableau ne contenant
        que des objets.
    """
    with Path(path).open("r", encoding="utf-8") as input_file:
        records = json.load(input_file)

    if not _is_record_array(records):
        raise ValueError(
            "Structure inattendue des données brutes : un tableau JSON ne "
            "contenant que des objets était attendu."
        )
    return records
