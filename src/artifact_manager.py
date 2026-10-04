"""
Artifact Manager for KELVRA Device Lab.
Provides controlled, secure management of generated device artifacts:
screenshots, screen recordings, exported logs, and automation test reports.
Enforces strict path traversal defenses, storage quotas, and confirmation-gated deletions.
"""

import json
import logging
import os
import shutil
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("kelvra.device_lab.artifacts")


class ArtifactType(str, Enum):
    SCREENSHOT = "SCREENSHOT"
    RECORDING = "RECORDING"
    LOG_EXPORT = "LOG_EXPORT"
    AUTOMATION_REPORT = "AUTOMATION_REPORT"


class ArtifactRecord(BaseModel):
    artifact_id: str
    name: str
    artifact_type: ArtifactType
    file_format: str  # png, jpeg, mp4, txt, json
    device_id: str
    session_token: Optional[str] = None
    file_size_bytes: int = 0
    relative_path: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, str] = Field(default_factory=dict)


class StorageSummary(BaseModel):
    total_bytes_used: int
    quota_bytes: int
    quota_percent: float
    artifact_counts: Dict[str, int]
    total_artifacts: int


class ArtifactManager:
    """Manages filesystem storage, metadata cataloging, and quota enforcement for artifacts."""

    def __init__(self, base_dir: Optional[str] = None, quota_bytes: int = 500 * 1024 * 1024):
        if base_dir:
            self.base_dir = Path(base_dir).resolve()
        else:
            self.base_dir = (Path(__file__).parent.parent / "artifacts").resolve()

        self.quota_bytes = quota_bytes  # Default 500 MB
        self.screenshots_dir = self.base_dir / "screenshots"
        self.recordings_dir = self.base_dir / "recordings"
        self.logs_dir = self.base_dir / "logs"
        self.reports_dir = self.base_dir / "reports"

        self._catalog_file = self.base_dir / "catalog.json"
        self._records: Dict[str, ArtifactRecord] = {}

        self._ensure_directories()
        self._load_catalog()

    def _ensure_directories(self):
        for d in (self.screenshots_dir, self.recordings_dir, self.logs_dir, self.reports_dir):
            d.mkdir(parents=True, exist_ok=True)

    def _load_catalog(self):
        if self._catalog_file.exists():
            try:
                with open(self._catalog_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        rec = ArtifactRecord(**item)
                        # Verify file actually exists on disk
                        full_path = self.base_dir / rec.relative_path
                        if full_path.exists():
                            self._records[rec.artifact_id] = rec
            except Exception as e:
                logger.warning(f"Failed to load artifact catalog: {e}")

    def _save_catalog(self):
        try:
            with open(self._catalog_file, "w", encoding="utf-8") as f:
                json.dump([r.model_dump() for r in self._records.values()], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist artifact catalog: {e}")

    def _resolve_type_dir(self, a_type: ArtifactType) -> Path:
        if a_type == ArtifactType.SCREENSHOT:
            return self.screenshots_dir
        elif a_type == ArtifactType.RECORDING:
            return self.recordings_dir
        elif a_type == ArtifactType.LOG_EXPORT:
            return self.logs_dir
        elif a_type == ArtifactType.AUTOMATION_REPORT:
            return self.reports_dir
        return self.base_dir

    def _sanitize_filename(self, name: str) -> str:
        # Strip path separators, traversal dots, and invalid characters
        clean = Path(name).name
        clean = clean.replace("..", "").replace("/", "").replace("\\", "")
        # Only allow alphanumeric, underscore, hyphen, dot
        clean = "".join(c for c in clean if c.isalnum() or c in ("-", "_", "."))
        return clean or f"artifact_{uuid.uuid4().hex[:8]}"

    def save_artifact(
        self,
        name: str,
        artifact_type: ArtifactType,
        file_format: str,
        data: bytes,
        device_id: str,
        session_token: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> ArtifactRecord:
        """Saves binary data as a tracked artifact with storage quota enforcement."""
        # 1. Enforce quota before saving
        data_size = len(data)
        current_size = self.get_total_size_bytes()
        if current_size + data_size > self.quota_bytes:
            # Trigger LRU prune of oldest artifacts
            self._prune_quota(data_size)

        # 2. Generate unique artifact ID and safe filename
        artifact_id = f"art-{uuid.uuid4().hex[:12]}"
        safe_name = self._sanitize_filename(name)
        if not safe_name.endswith(f".{file_format}"):
            safe_name = f"{safe_name}.{file_format}"

        stored_filename = f"{artifact_id}_{safe_name}"
        type_dir = self._resolve_type_dir(artifact_type)
        target_path = (type_dir / stored_filename).resolve()

        # Path traversal defense
        if not str(target_path).startswith(str(self.base_dir)):
            raise ValueError(f"Security error: Artifact path traversal detected '{target_path}'")

        # Write data to disk
        with open(target_path, "wb") as f:
            f.write(data)

        # Build relative path
        rel_path = target_path.relative_to(self.base_dir).as_posix()

        rec = ArtifactRecord(
            artifact_id=artifact_id,
            name=safe_name,
            artifact_type=artifact_type,
            file_format=file_format.lower(),
            device_id=device_id,
            session_token=session_token,
            file_size_bytes=data_size,
            relative_path=rel_path,
            metadata=metadata or {}
        )
        self._records[artifact_id] = rec
        self._save_catalog()

        logger.info(f"Saved artifact {artifact_id} ({safe_name}, {data_size} bytes)")
        return rec

    def get_artifact(self, artifact_id: str) -> Optional[ArtifactRecord]:
        return self._records.get(artifact_id)

    def get_artifact_file_path(self, artifact_id: str) -> Optional[Path]:
        rec = self._records.get(artifact_id)
        if not rec:
            return None
        full_path = (self.base_dir / rec.relative_path).resolve()
        # Security sanity check
        if not str(full_path).startswith(str(self.base_dir)) or not full_path.exists():
            return None
        return full_path

    def list_artifacts(
        self,
        artifact_type: Optional[ArtifactType] = None,
        device_id: Optional[str] = None,
        limit: int = 100
    ) -> List[ArtifactRecord]:
        records = list(self._records.values())
        if artifact_type:
            records = [r for r in records if r.artifact_type == artifact_type]
        if device_id:
            records = [r for r in records if r.device_id == device_id or r.device_id.endswith(f":{device_id}")]
        # Sort newest first
        records.sort(key=lambda r: r.created_at, reverse=True)
        return records[:limit]

    def delete_artifact(self, artifact_id: str, confirm: bool = False) -> bool:
        """Deletes an artifact from disk and catalog. Requires explicit confirmation."""
        if not confirm:
            raise ValueError("Explicit confirmation parameter (confirm=True) is required to delete artifacts.")

        rec = self._records.get(artifact_id)
        if not rec:
            return False

        full_path = (self.base_dir / rec.relative_path).resolve()
        if str(full_path).startswith(str(self.base_dir)) and full_path.exists():
            try:
                os.remove(full_path)
            except Exception as e:
                logger.error(f"Error removing artifact file '{full_path}': {e}")
                return False

        del self._records[artifact_id]
        self._save_catalog()
        logger.info(f"Deleted artifact {artifact_id}")
        return True

    def get_total_size_bytes(self) -> int:
        return sum(r.file_size_bytes for r in self._records.values())

    def get_storage_summary(self) -> StorageSummary:
        total = self.get_total_size_bytes()
        pct = round((total / self.quota_bytes) * 100.0, 2) if self.quota_bytes > 0 else 0.0
        counts: Dict[str, int] = {}
        for r in self._records.values():
            counts[r.artifact_type.value] = counts.get(r.artifact_type.value, 0) + 1

        return StorageSummary(
            total_bytes_used=total,
            quota_bytes=self.quota_bytes,
            quota_percent=pct,
            artifact_counts=counts,
            total_artifacts=len(self._records)
        )

    def _prune_quota(self, needed_bytes: int):
        """Prune oldest artifacts until needed bytes fit under quota."""
        # Sort oldest first
        sorted_records = sorted(self._records.values(), key=lambda r: r.created_at)
        for rec in sorted_records:
            if self.get_total_size_bytes() + needed_bytes <= self.quota_bytes:
                break
            try:
                self.delete_artifact(rec.artifact_id, confirm=True)
            except Exception:
                pass
