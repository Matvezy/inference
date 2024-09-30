from multiprocessing import Process

from inference.core.cache import cache
from inference.core.interfaces.http.http_api import HttpInterface
from inference.core.interfaces.stream_manager.manager_app.app import start
from inference.core.managers.active_learning import ActiveLearningManager, BackgroundTaskActiveLearningManager
from inference.core.managers.base import ModelManager
from inference.core.managers.decorators.fixed_size_cache import WithFixedSizeCache
from inference.core.registries.roboflow import (
    RoboflowModelRegistry,
)
import os
from prometheus_fastapi_instrumentator import Instrumentator

from inference.core.env import MAX_ACTIVE_MODELS, ACTIVE_LEARNING_ENABLED, LAMBDA, ENABLE_STREAM_API
from inference.models.utils import ROBOFLOW_MODEL_TYPES

model_registry = RoboflowModelRegistry(ROBOFLOW_MODEL_TYPES)

if ACTIVE_LEARNING_ENABLED:
    if LAMBDA:
        model_manager = ActiveLearningManager(model_registry=model_registry, cache=cache)
    else:
        model_manager = BackgroundTaskActiveLearningManager(model_registry=model_registry, cache=cache)
else:
    model_manager = ModelManager(model_registry=model_registry)

model_manager = WithFixedSizeCache(
    model_manager,
    max_size=MAX_ACTIVE_MODELS
)
model_manager.init_pingback()
interface = HttpInterface(model_manager)
app = interface.app
# Setup Prometheus scraping endpoint at /metrics
# More info: https://github.com/trallnag/prometheus-fastapi-instrumentator
if os.environ.get("ENABLE_PROMETHEUS", False):
    instrumentor = Instrumentator()
    instrumentor.instrument(app).expose(app)

    @app.on_event("startup")
    async def _startup():
        instrumentor.expose(app)

if ENABLE_STREAM_API:
    stream_manager_process = Process(
        target=start,
    )
    stream_manager_process.start()
