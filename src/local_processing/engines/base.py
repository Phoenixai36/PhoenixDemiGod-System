from abc import ABC, abstractmethod
from typing import Any, Dict

from src.local_processing.model_manager import ModelMetadata


class InferenceEngine(ABC):
    @abstractmethod
    def can_load(self, metadata: ModelMetadata) -> bool:
        """Verifica si este motor puede cargar el modelo dado."""
        pass

    @abstractmethod
    async def load_model(self, metadata: ModelMetadata) -> Any:
        """Carga el modelo en memoria."""
        pass

    @abstractmethod
    async def predict(self, model: Any, data: Any, options: Dict) -> Any:
        """Ejecuta la inferencia."""
        pass