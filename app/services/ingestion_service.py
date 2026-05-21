"""
Ingestion pipeline: normalise → embed → upsert into Qdrant.
"""

import time
from typing import Any, Dict, List

from pydantic import ValidationError
from qdrant_client.models import PointStruct

from app.config.settings import settings
from app.db.qdrant_client import create_collection_if_not_exists, get_qdrant_client
from app.schemas.incident import IncidentRecord
from app.services.embedding_service import generate_embedding
from app.services.incident_normalizer import normalize_incident

DEFAULT_BATCH_SIZE = 5
INTER_BATCH_DELAY  = 1.0
MAX_RETRIES        = 3
RETRY_DELAY_SECONDS = 3.0


def _to_incident_record(incident: Any) -> IncidentRecord:
    if isinstance(incident, IncidentRecord):
        return incident
    if isinstance(incident, dict):
        return IncidentRecord.model_validate(incident)
    raise TypeError("Incident must be an IncidentRecord or dictionary.")


def _build_payload(incident: IncidentRecord, normalized: Dict[str, Any]) -> Dict[str, Any]:
    metadata = normalized["metadata"]
    return {
        "sys_id":           metadata["sys_id"],
        "number":           metadata["number"],
        "short_description": incident.short_description,
        "description":      incident.description,
        "assignment_group": metadata["assignment_group"],
        "priority":         metadata["priority"],
        "category":         metadata["category"],
        "state":            metadata["state"],
        "resolution_notes": incident.resolution_notes,
        "opened_at":        metadata["opened_at"],
        "sys_created_on":   metadata["sys_created_on"],
        "servicenow_link":  incident.servicenow_link,
        "azure_devops_link": incident.azure_devops_link,
        "datafix_code":     incident.datafix_code,
    }


def _batched(items: List[PointStruct], batch_size: int) -> List[List[PointStruct]]:
    return [items[i : i + batch_size] for i in range(0, len(items), batch_size)]


def _upsert_with_retry(client, points: List[PointStruct], batch_num: int) -> None:
    last_exc: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            client.upsert(collection_name=settings.QDRANT_COLLECTION_NAME, points=points)
            return
        except Exception as exc:
            last_exc = exc
            delay = RETRY_DELAY_SECONDS * attempt
            if attempt < MAX_RETRIES:
                print(f"  Batch {batch_num} attempt {attempt}/{MAX_RETRIES} failed: {exc}. Retrying in {delay:.0f}s…")
                time.sleep(delay)
            else:
                print(f"  Batch {batch_num} attempt {attempt}/{MAX_RETRIES} failed: {exc}. Giving up.")
    raise RuntimeError(f"Upsert failed after {MAX_RETRIES} attempts.") from last_exc


def ingest_incidents(incidents: list, batch_size: int = DEFAULT_BATCH_SIZE) -> Dict[str, int]:
    if batch_size < 1:
        raise ValueError("batch_size must be greater than zero.")

    points: List[PointStruct] = []
    summary = {"received": len(incidents), "prepared": 0, "inserted": 0, "skipped": 0, "failed": 0}

    for incident_data in incidents:
        try:
            incident   = _to_incident_record(incident_data)
            if not incident.sys_id:
                summary["skipped"] += 1
                continue
            normalized = normalize_incident(incident)
            print(f"Generating embedding for incident {incident.number}.")
            embedding  = generate_embedding(normalized["text"])
            payload    = _build_payload(incident, normalized)
            points.append(PointStruct(id=incident.sys_id, vector=embedding, payload=payload))
            summary["prepared"] += 1
        except (TypeError, ValidationError, ValueError) as exc:
            print(f"Skipped invalid incident: {exc}")
            summary["skipped"] += 1
        except Exception as exc:
            print(f"Failed to prepare incident embedding: {exc}")
            summary["failed"] += 1

    if not points:
        return summary

    try:
        create_collection_if_not_exists()
        client = get_qdrant_client()
    except Exception as exc:
        print(f"Failed to initialise Qdrant collection: {exc}")
        summary["failed"] += len(points)
        return summary

    batches = _batched(points, batch_size)
    print(f"Upserting {len(points)} points in {len(batches)} batch(es) of ≤{batch_size}…")

    for batch_num, batch in enumerate(batches, start=1):
        print(f"  Batch {batch_num}/{len(batches)}: {len(batch)} points…")
        try:
            _upsert_with_retry(client, batch, batch_num)
            summary["inserted"] += len(batch)
            print(f"  Batch {batch_num}/{len(batches)}: OK ({summary['inserted']} total inserted)")
        except Exception as exc:
            summary["failed"] += len(batch)
            print(f"  Batch {batch_num}/{len(batches)}: permanently failed — {exc}")

        if batch_num < len(batches):
            time.sleep(INTER_BATCH_DELAY)

    return summary