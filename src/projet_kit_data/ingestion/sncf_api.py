'Récupère et conserve les observations mensuelles brutes de régularité TGV SNCF.'

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
    """Représente un échec HTTP ou une structure de réponse invalide de l’API SNCF.
    
    :param message: Description de l’échec de l’API.
    :type message: str"""

    def __init__(self, message: str) -> None:
        """Initialise l’erreur de l’API avec un message descriptif.
        
        :param message: Description de l’échec de l’API.
        :type message: str
        :returns: Aucune valeur.
        :rtype: None"""
        super().__init__(message)


def _is_record_array(value: Any) -> TypeGuard[list[dict[str, Any]]]:
    'Indique si *value* est un tableau JSON contenant uniquement des objets.'
    return isinstance(value, list) and all(isinstance(record, dict) for record in value)


def _retry_after_seconds(value: str | None) -> float | None:
    'Interprète la valeur HTTP Retry-After comme un délai positif ou nul.'
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
    'Attend selon un délai exponentiel en respectant une valeur Retry-After valide.'
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
    """Récupère toutes les observations de régularité TGV SNCF sans les transformer.
    
    Appelle l’export JSON de l’API SNCF Explore v2.1 avec ``limit=-1``. Les erreurs
    transitoires de connexion, délais dépassés et réponses HTTP 429 ou 5xx entraînent
    jusqu’à ``max_retries`` nouvelles tentatives.
    
    :param connect_timeout: Délai maximal de connexion en secondes.
    :type connect_timeout: float
    :param read_timeout: Délai maximal de lecture de la réponse en secondes.
    :type read_timeout: float
    :param max_retries: Nombre de nouvelles tentatives après la requête initiale.
    :type max_retries: int
    :param backoff_factor: Délai de base en secondes pour l’attente exponentielle.
    :type backoff_factor: float
    :returns: Liste de dictionnaires conservant les noms et valeurs des champs JSON.
    :rtype: list[dict[str, Any]]
    :raises SNCFAPIError: Si les tentatives échouent, si le statut ne permet pas de réessayer ou si le JSON n’est pas un tableau d’objets.
    :raises requests.exceptions.JSONDecodeError: Si la réponse n’est pas du JSON valide ; cette exception est volontairement propagée.
    :raises ValueError: Si un délai, nombre de tentatives ou facteur d’attente est invalide."""
    if connect_timeout <= 0 or read_timeout <= 0:
        raise ValueError('Les délais d’attente doivent être strictement positifs.')
    if max_retries < 0:
        raise ValueError('max_retries doit être positif ou nul.')
    if backoff_factor < 0:
        raise ValueError('backoff_factor doit être positif ou nul.')

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
                f"La requête vers l’API SNCF a échoué après {max_retries} nouvelles tentatives : {exc}"
            ) from exc
        except requests.RequestException as exc:
            raise SNCFAPIError(f"Échec de la requête vers l’API SNCF : {exc}") from exc

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
                    f"L’API SNCF a renvoyé le statut HTTP {response.status_code} after "
                    f"{max_retries} nouvelles tentatives."
                ) from exc
            raise SNCFAPIError(
                f"L’API SNCF a renvoyé un statut HTTP permettant une nouvelle tentative : {response.status_code} "
                f"after {max_retries} nouvelles tentatives."
            )

        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise SNCFAPIError(
                f"L’API SNCF a renvoyé le statut HTTP {response.status_code}: {exc}"
            ) from exc

        records = response.json()
        if not _is_record_array(records):
            raise SNCFAPIError(
                "Unexpected SNCF API response: expected a JSON array "
                "containing only objects."
            )
        return records

    raise SNCFAPIError('La requête vers l’API SNCF a échoué sans réponse.')


def save_raw_data(
    records: Sequence[dict[str, Any]],
    path: str | os.PathLike[str] = DEFAULT_RAW_DATA_PATH,
) -> Path:
    """Enregistre atomiquement les observations brutes dans un tableau JSON UTF-8.
    
    Crée les dossiers parents si nécessaire. Un fichier temporaire du dossier cible
    est déplacé avec :func:`os.replace` afin de ne pas exposer de fichier partiellement écrit.
    
    :param records: Dictionnaires bruts à sérialiser sans ETL ni nettoyage.
    :type records: Sequence[dict[str, Any]]
    :param path: Destination ; chemin des données brutes du projet par défaut.
    :type path: str | os.PathLike[str]
    :returns: Chemin du fichier de destination.
    :rtype: pathlib.Path
    :raises OSError: Si la création des dossiers, l’écriture ou le remplacement échoue. Le fichier temporaire est supprimé si possible avant de propager l’erreur.
    :raises TypeError: Si une valeur ne peut pas être encodée en JSON."""
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
    """Charge un tableau JSON brut SNCF précédemment enregistré.
    
    :param path: Fichier JSON ; chemin des données brutes du projet par défaut.
    :type path: str | os.PathLike[str]
    :returns: Dictionnaires décodés conservant les noms et valeurs des champs sources.
    :rtype: list[dict[str, Any]]
    :raises OSError: Si le fichier est illisible, notamment :class:`FileNotFoundError` s’il est absent.
    :raises json.JSONDecodeError: Si le JSON est invalide.
    :raises ValueError: Si le JSON décodé n’est pas un tableau contenant uniquement des objets."""
    with Path(path).open("r", encoding="utf-8") as input_file:
        records = json.load(input_file)

    if not _is_record_array(records):
        raise ValueError(
            "Unexpected raw data structure: expected a JSON array "
            "containing only objects."
        )
    return records
