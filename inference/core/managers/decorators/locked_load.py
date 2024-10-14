from typing import Optional

from inference.core.cache import cache
from inference.core.managers.decorators.base import ModelManagerDecorator
from inference.core.profiling.core import InferenceProfiler

lock_str = lambda z: f"locks:model-load:{z}"


class LockedLoadModelManagerDecorator(ModelManagerDecorator):
    """Must acquire lock to load model"""

    def add_model(
        self,
        model_id: str,
        api_key: str,
        model_id_alias: Optional[str] =None,
        profiler: Optional[InferenceProfiler] = None,
    ):
        with cache.lock(lock_str(model_id), expire=180.0):
            return super().add_model(model_id, api_key, model_id_alias=model_id_alias, profiler=profiler)
