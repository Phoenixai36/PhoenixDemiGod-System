"""
Local Model Storage and Management System

This module provides the infrastructure for storing, versioning, and managing
AI models locally without cloud dependencies. It implements a robust system
for model lifecycle management, integrity checking, and hot-swapping.
"""

import asyncio
import hashlib
import json
import logging
import shutil
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from .engines.base import InferenceEngine

logger = logging.getLogger(__name__)


class ModelStatus(Enum):
    """Model status enumeration."""

    AVAILABLE = "available"
    LOADING = "loading"
    ACTIVE = "active"
    CORRUPTED = "corrupted"
    DEPRECATED = "deprecated"


@dataclass
class ModelMetadata:
    """Metadata for a local AI model."""

    name: str
    version: str
    model_type: str  # "mamba", "ssm", "fallback"
    file_path: str
    checksum: str
    size_bytes: int
    performance_profile: Dict[str, Any]
    dependencies: List[str]
    created_at: datetime
    last_used: Optional[datetime] = None
    usage_count: int = 0
    status: ModelStatus = ModelStatus.AVAILABLE


class LocalModelManager:
    """
    Manages local AI model storage, versioning, and lifecycle.

    This class provides the core infrastructure for Phoenix Hydra's
    offline-first AI processing capabilities.
    """

    def __init__(
        self, models_dir: Path = Path("models"), db_path: Path = Path("models.db")
    ):
        self.models_dir = Path(models_dir)
        self.db_path = Path(db_path)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self._init_database()
        self._active_models: Dict[str, Any] = {}
        self._inference_engines: List["InferenceEngine"] = []

    def _init_database(self):
        """Initialize the SQLite database for model metadata."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS models (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    model_type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    performance_profile TEXT NOT NULL,
                    dependencies TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_used TEXT,
                    usage_count INTEGER DEFAULT 0,
                    status TEXT NOT NULL,
                    UNIQUE(name, version)
                )
            """)
            conn.commit()

    def register_model(self, model_path: Path, metadata: ModelMetadata) -> bool:
        """
        Register a new model in the local storage system.

        Args:
            model_path: Path to the model file
            metadata: Model metadata

        Returns:
            bool: True if registration successful
        """
        try:
            # Verify file exists and calculate checksum
            if not model_path.exists():
                logger.error(f"Model file not found: {model_path}")
                return False

            checksum = self._calculate_checksum(model_path)
            if checksum != metadata.checksum:
                logger.error(f"Checksum mismatch for {model_path}")
                return False

            # Copy to models directory
            dest_path = self.models_dir / f"{metadata.name}-{metadata.version}"
            dest_path.mkdir(parents=True, exist_ok=True)
            model_dest = dest_path / model_path.name
            shutil.copy2(model_path, model_dest)

            # Update metadata with actual path
            metadata.file_path = str(model_dest)

            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO models
                    (name, version, model_type, file_path, checksum, size_bytes,
                     performance_profile, dependencies, created_at, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        metadata.name,
                        metadata.version,
                        metadata.model_type,
                        metadata.file_path,
                        metadata.checksum,
                        metadata.size_bytes,
                        json.dumps(metadata.performance_profile),
                        json.dumps(metadata.dependencies),
                        metadata.created_at.isoformat(),
                        metadata.status.value,
                    ),
                )
                conn.commit()

            logger.info(
                f"Successfully registered model: {metadata.name}-{metadata.version}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to register model: {e}")
            return False

    def get_model_metadata(
        self, name: str, version: Optional[str] = None
    ) -> Optional[ModelMetadata]:
        """
        Retrieve model metadata.

        Args:
            name: Model name
            version: Specific version (if None, returns latest)

        Returns:
            ModelMetadata or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            if version:
                cursor = conn.execute(
                    """
                    SELECT * FROM models WHERE name = ? AND version = ?
                """,
                    (name, version),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT * FROM models WHERE name = ?
                    ORDER BY created_at DESC LIMIT 1
                """,
                    (name,),
                )

            row = cursor.fetchone()
            if not row:
                return None

            return self._row_to_metadata(row)

    def list_models(self, model_type: Optional[str] = None) -> List[ModelMetadata]:
        """
        List all available models.

        Args:
            model_type: Filter by model type

        Returns:
            List of model metadata
        """
        with sqlite3.connect(self.db_path) as conn:
            if model_type:
                cursor = conn.execute(
                    """
                    SELECT * FROM models WHERE model_type = ? ORDER BY name, version
                """,
                    (model_type,),
                )
            else:
                cursor = conn.execute("""
                    SELECT * FROM models ORDER BY name, version
                """)

            return [self._row_to_metadata(row) for row in cursor.fetchall()]

    def register_inference_engine(self, engine: "InferenceEngine") -> None:
        """Registers an inference engine."""
        self._inference_engines.append(engine)

    async def load_model(
        self, name: str, version: Optional[str] = None
    ) -> Optional[Any]:
        """
        Load a model into memory for inference.

        Args:
            name: Model name
            version: Specific version

        Returns:
            Loaded model object or None if failed
        """
        metadata = self.get_model_metadata(name, version)
        if not metadata:
            logger.error(f"Model not found: {name}-{version}")
            return None

        # Check if already loaded
        model_key = f"{name}-{metadata.version}"
        if model_key in self._active_models:
            await self._update_usage_stats(metadata)
            return self._active_models[model_key]

        try:
            # Update status to loading
            self._update_model_status(metadata, ModelStatus.LOADING)

            # Verify integrity before loading
            if not self._verify_model_integrity(metadata):
                logger.error(f"Model integrity check failed: {model_key}")
                self._update_model_status(metadata, ModelStatus.CORRUPTED)
                return None

            # Find appropriate inference engine
            engine: Optional["InferenceEngine"] = next(
                (e for e in self._inference_engines if e.can_load(metadata)), None
            )
            if engine is None:
                logger.error(
                    f"No inference engine found for model type: {metadata.model_type}"
                )
                return None

            # Load model using the engine
            model = await engine.load_model(metadata)
            if model:
                self._active_models[model_key] = model
                self._update_model_status(metadata, ModelStatus.ACTIVE)
                await self._update_usage_stats(metadata)
                logger.info(f"Successfully loaded model: {model_key}")
                return model
            else:
                self._update_model_status(metadata, ModelStatus.CORRUPTED)
                return None

        except Exception as e:
            logger.error(f"Failed to load model {model_key}: {e}")
            self._update_model_status(metadata, ModelStatus.CORRUPTED)
            return None

    def unload_model(self, name: str, version: Optional[str] = None) -> bool:
        """
        Unload a model from memory.

        Args:
            name: Model name
            version: Specific version

        Returns:
            bool: True if successfully unloaded
        """
        metadata = self.get_model_metadata(name, version)
        if not metadata:
            return False

        model_key = f"{name}-{metadata.version}"
        if model_key in self._active_models:
            del self._active_models[model_key]
            self._update_model_status(metadata, ModelStatus.AVAILABLE)
            logger.info(f"Unloaded model: {model_key}")
            return True

        return False

    def get_fallback_model(self, model_type: str) -> Optional[ModelMetadata]:
        """
        Get the best available fallback model for a given type.

        Args:
            model_type: Type of model needed

        Returns:
            ModelMetadata for fallback model or None
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT * FROM models
                WHERE model_type = ? AND status = 'available'
                ORDER BY size_bytes ASC, usage_count DESC
                LIMIT 1
            """,
                (model_type,),
            )

            row = cursor.fetchone()
            return self._row_to_metadata(row) if row else None

    def cleanup_unused_models(self, days_unused: int = 30) -> int:
        """
        Clean up models that haven't been used recently.

        Args:
            days_unused: Number of days of non-use before cleanup

        Returns:
            Number of models cleaned up
        """
        cutoff_date = datetime.now().timestamp() - (days_unused * 24 * 3600)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT file_path FROM models
                WHERE (last_used IS NULL OR last_used < ?)
                AND status != 'active'
            """,
                (datetime.fromtimestamp(cutoff_date).isoformat(),),
            )

            cleanup_count = 0
            for (file_path,) in cursor.fetchall():
                try:
                    Path(file_path).unlink(missing_ok=True)
                    cleanup_count += 1
                except Exception as e:
                    logger.warning(f"Failed to delete {file_path}: {e}")

            # Remove from database
            conn.execute(
                """
                DELETE FROM models
                WHERE (last_used IS NULL OR last_used < ?)
                AND status != 'active'
            """,
                (datetime.fromtimestamp(cutoff_date).isoformat(),),
            )
            conn.commit()

        logger.info(f"Cleaned up {cleanup_count} unused models")
        return cleanup_count

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def _verify_model_integrity(self, metadata: ModelMetadata) -> bool:
        """Verify model file integrity using checksum."""
        try:
            current_checksum = self._calculate_checksum(Path(metadata.file_path))
            return current_checksum == metadata.checksum
        except Exception as e:
            logger.error(f"Integrity check failed for {metadata.name}: {e}")
            return False

    # async def _load_model_file(self, metadata: ModelMetadata) -> Optional[Any]:
    #     """
    #     Load the actual model file. This would be implemented based on
    #     the specific model format (Mamba, SSM, etc.).
    #     """
    #     # Placeholder for actual model loading logic
    #     # This would integrate with the specific AI framework being used
    #     await asyncio.sleep(0.1)  # Simulate loading time
    #     return {"model_path": metadata.file_path, "metadata": metadata}

    def _update_model_status(self, metadata: ModelMetadata, status: ModelStatus):
        """Update model status in database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE models SET status = ? WHERE name = ? AND version = ?
            """,
                (status.value, metadata.name, metadata.version),
            )
            conn.commit()

    async def _update_usage_stats(self, metadata: ModelMetadata):
        """Update model usage statistics."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE models
                SET last_used = ?, usage_count = usage_count + 1
                WHERE name = ? AND version = ?
            """,
                (datetime.now().isoformat(), metadata.name, metadata.version),
            )
            conn.commit()

    def _row_to_metadata(self, row) -> ModelMetadata:
        """Convert database row to ModelMetadata object."""
        return ModelMetadata(
            name=row[1],
            version=row[2],
            model_type=row[3],
            file_path=row[4],
            checksum=row[5],
            size_bytes=row[6],
            performance_profile=json.loads(row[7]),
            dependencies=json.loads(row[8]),
            created_at=datetime.fromisoformat(row[9]),
            last_used=datetime.fromisoformat(row[10]) if row[10] else None,
            usage_count=row[11],
            status=ModelStatus(row[12]),
        )
