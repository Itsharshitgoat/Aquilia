"""
Model Loader — lazy loading, hot reload, and lifecycle state management.

The loader is responsible for actually instantiating model classes,
calling ``load()``, and managing the ``ModelState`` FSM.

Key behaviors:
- **Lazy loading**: models load on first prediction request
- **Hot reload**: swap to a new version atomically
- **Warmup**: run N synthetic requests after load
- **Concurrency safety**: asyncio.Lock per model prevents double loads

Usage::

    loader = ModelLoader(registry, device_manager, executor)
    instance = await loader.ensure_loaded("sentiment", "v1")
    await loader.hot_reload("sentiment", "v2")
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from ..runtime.base import ModelState
from ..engine.hooks import HookRegistry, collect_hooks
from ..engine.pipeline import InferencePipeline
from .registry import ModelEntry, ModelRegistry

logger = logging.getLogger("aquilia.mlops.orchestrator.loader")


class LoadedModel:
    """
    Container for a loaded model instance and its associated resources.

    Holds the model instance, its hook registry, inference pipeline,
    and runtime. This is what ``ModelLoader.ensure_loaded()`` returns.
    """

    __slots__ = (
        "entry", "instance", "hooks", "pipeline",
        "load_time_ms", "loaded_at",
    )

    def __init__(
        self,
        entry: ModelEntry,
        instance: Any,
        hooks: HookRegistry,
        pipeline: InferencePipeline,
        load_time_ms: float,
    ) -> None:
        self.entry = entry
        self.instance = instance
        self.hooks = hooks
        self.pipeline = pipeline
        self.load_time_ms = load_time_ms
        self.loaded_at = time.time()


class ModelLoader:
    """
    Manages model instantiation, loading, unloading, and hot reload.

    Each model version has at most one loaded instance at a time.
    Loading is lazy (happens on first request) and protected by
    per-model locks to prevent double loads.
    """

    def __init__(
        self,
        registry: ModelRegistry,
        device_manager: Any = None,
        executor: Any = None,
        metrics_collector: Any = None,
    ) -> None:
        self._registry = registry
        self._device_manager = device_manager
        self._executor = executor
        self._metrics = metrics_collector
        self._loaded: Dict[str, LoadedModel] = {}   # "name:version" → LoadedModel
        self._locks: Dict[str, asyncio.Lock] = {}

    def _get_lock(self, key: str) -> asyncio.Lock:
        """Get or create a per-model lock."""
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]

    # ── Lazy Loading ─────────────────────────────────────────────────

    async def ensure_loaded(self, name: str, version: str) -> LoadedModel:
        """
        Ensure a model is loaded and return its ``LoadedModel``.

        If the model is already loaded, returns immediately.
        If not, acquires the model lock and loads it.

        Raises:
            KeyError: Model not found in registry.
            RuntimeError: Load failed (state → FAILED).
        """
        key = f"{name}:{version}"

        # Fast path — already loaded
        loaded = self._loaded.get(key)
        if loaded and loaded.entry.state == ModelState.LOADED:
            return loaded

        # Slow path — acquire lock and load
        lock = self._get_lock(key)
        async with lock:
            # Double-check after acquiring lock
            loaded = self._loaded.get(key)
            if loaded and loaded.entry.state == ModelState.LOADED:
                return loaded

            entry = self._registry.get(name, version)
            if entry is None:
                raise KeyError(f"Model '{name}:{version}' not found in registry")

            return await self._load_model(entry)

    async def _load_model(self, entry: ModelEntry) -> LoadedModel:
        """Instantiate and load a model from its registry entry."""
        key = entry.key
        self._registry.update_state(entry.name, entry.version, ModelState.LOADING)

        start = time.monotonic()
        try:
            # Instantiate the model class
            instance = self._instantiate(entry)

            # Collect hooks from the instance
            hooks = collect_hooks(instance)

            # Determine device
            device = entry.config.device
            if self._device_manager and device == "auto":
                device = await self._device_manager.select_device()

            # Call the model's load method if it exists
            if hasattr(instance, "load") and callable(instance.load):
                load_fn = instance.load
                if inspect.iscoroutinefunction(load_fn):
                    await load_fn(entry.config.artifacts_dir, device)
                else:
                    load_fn(entry.config.artifacts_dir, device)

            # Call on_load hooks
            for hook in hooks.on_load:
                if inspect.iscoroutinefunction(hook):
                    await hook()
                else:
                    hook()

            # Build the inference pipeline
            # If the instance IS a runtime (has infer()), use it directly
            # Otherwise, wrap the instance's predict() in a minimal runtime
            runtime = self._get_runtime_for_instance(instance)
            pipeline = InferencePipeline(
                runtime=runtime,
                hooks=hooks,
                metrics_collector=self._metrics,
                executor=self._executor,
            )

            load_time_ms = (time.monotonic() - start) * 1000
            entry.state = ModelState.LOADED

            loaded = LoadedModel(
                entry=entry,
                instance=instance,
                hooks=hooks,
                pipeline=pipeline,
                load_time_ms=load_time_ms,
            )
            self._loaded[key] = loaded

            self._registry.update_state(entry.name, entry.version, ModelState.LOADED)
            logger.info(
                "Model %s loaded in %.1fms (device=%s)", key, load_time_ms, device,
            )
            return loaded

        except Exception as exc:
            self._registry.update_state(entry.name, entry.version, ModelState.FAILED)
            logger.error("Failed to load model %s: %s", key, exc)
            raise

    def _instantiate(self, entry: ModelEntry) -> Any:
        """Create an instance of the model class."""
        cls = entry.model_class

        # If it's already an instance (functional model), return directly
        if not isinstance(cls, type):
            return cls

        # Try to instantiate with no args
        try:
            return cls()
        except TypeError:
            # Some classes might need config
            try:
                return cls(config=entry.config)
            except TypeError:
                return cls()

    def _get_runtime_for_instance(self, instance: Any) -> Any:
        """Get or create a runtime adapter for the model instance."""
        from ..runtime.base import BaseRuntime

        # If the instance IS a runtime, use it
        if isinstance(instance, BaseRuntime):
            return instance

        # Otherwise, create a wrapper runtime
        return _InstanceRuntimeAdapter(instance)

    # ── Hot Reload ───────────────────────────────────────────────────

    async def hot_reload(self, name: str, new_version: str) -> LoadedModel:
        """
        Hot-reload a model to a new version.

        Loads the new version first, then atomically swaps, then unloads
        the old version. This ensures zero downtime.

        Returns:
            The newly loaded ``LoadedModel``.
        """
        # Load new version (this doesn't affect current serving)
        new_loaded = await self.ensure_loaded(name, new_version)

        # Find and unload old versions
        old_keys = [
            k for k in self._loaded
            if k.startswith(f"{name}:") and k != f"{name}:{new_version}"
        ]
        for old_key in old_keys:
            old = self._loaded.pop(old_key, None)
            if old:
                await self._unload_instance(old)

        # Update active version in registry
        await self._registry.set_active_version(name, new_version)

        logger.info("Hot-reloaded %s to version %s", name, new_version)
        return new_loaded

    # ── Unloading ────────────────────────────────────────────────────

    async def unload(self, name: str, version: str) -> bool:
        """Unload a specific model version."""
        key = f"{name}:{version}"
        lock = self._get_lock(key)
        async with lock:
            loaded = self._loaded.pop(key, None)
            if loaded is None:
                return False
            await self._unload_instance(loaded)
            self._registry.update_state(name, version, ModelState.UNLOADED)
            return True

    async def unload_all(self) -> None:
        """Unload all loaded models (shutdown)."""
        keys = list(self._loaded.keys())
        for key in keys:
            loaded = self._loaded.pop(key, None)
            if loaded:
                await self._unload_instance(loaded)
                self._registry.update_state(
                    loaded.entry.name, loaded.entry.version, ModelState.UNLOADED,
                )

    async def _unload_instance(self, loaded: LoadedModel) -> None:
        """Unload a single model instance."""
        try:
            # Call on_unload hooks
            for hook in loaded.hooks.on_unload:
                if inspect.iscoroutinefunction(hook):
                    await hook()
                else:
                    hook()

            # Call instance unload if available
            if hasattr(loaded.instance, "unload") and callable(loaded.instance.unload):
                if inspect.iscoroutinefunction(loaded.instance.unload):
                    await loaded.instance.unload()
                else:
                    loaded.instance.unload()

            logger.info("Unloaded model %s", loaded.entry.key)

        except Exception as exc:
            logger.error("Error unloading model %s: %s", loaded.entry.key, exc)

    # ── Queries ──────────────────────────────────────────────────────

    def is_loaded(self, name: str, version: str) -> bool:
        """Check if a model version is currently loaded."""
        key = f"{name}:{version}"
        loaded = self._loaded.get(key)
        return loaded is not None and loaded.entry.state == ModelState.LOADED

    def get_loaded(self, name: str, version: str) -> Optional[LoadedModel]:
        """Get a loaded model instance if available."""
        return self._loaded.get(f"{name}:{version}")

    def loaded_models(self) -> List[str]:
        """List all currently loaded model keys."""
        return list(self._loaded.keys())

    def summary(self) -> Dict[str, Any]:
        """Summary for health endpoints."""
        return {
            "loaded_count": len(self._loaded),
            "models": {
                key: {
                    "state": lm.entry.state.value,
                    "load_time_ms": round(lm.load_time_ms, 1),
                    "loaded_at": lm.loaded_at,
                }
                for key, lm in self._loaded.items()
            },
        }


# ── Instance Runtime Adapter ─────────────────────────────────────────────

class _InstanceRuntimeAdapter:
    """
    Wraps an AquiliaModel instance as a runtime-compatible object.

    This adapter allows the InferencePipeline to call infer() on any
    model instance that has a predict() method.
    """

    def __init__(self, instance: Any) -> None:
        self._instance = instance
        self._state = ModelState.LOADED

    @property
    def state(self) -> ModelState:
        return self._state

    @property
    def is_loaded(self) -> bool:
        return self._state == ModelState.LOADED

    async def preprocess(self, raw_input: Dict[str, Any]) -> Dict[str, Any]:
        if hasattr(self._instance, "preprocess") and callable(self._instance.preprocess):
            fn = self._instance.preprocess
            if inspect.iscoroutinefunction(fn):
                return await fn(raw_input)
            return fn(raw_input)
        return raw_input

    async def postprocess(self, raw_output: Dict[str, Any]) -> Dict[str, Any]:
        if hasattr(self._instance, "postprocess") and callable(self._instance.postprocess):
            fn = self._instance.postprocess
            if inspect.iscoroutinefunction(fn):
                return await fn(raw_output)
            return fn(raw_output)
        return raw_output

    async def infer(self, batch: Any) -> list:
        from .._types import InferenceResult

        results = []
        for req in batch.requests:
            start = time.monotonic()
            try:
                predict_fn = getattr(self._instance, "predict", None)
                if predict_fn is None:
                    predict_fn = getattr(self._instance, "__call__", None)
                if predict_fn is None:
                    raise RuntimeError(
                        f"Model {type(self._instance).__name__} has no predict() or __call__() method"
                    )

                if inspect.iscoroutinefunction(predict_fn):
                    outputs = await predict_fn(req.inputs)
                else:
                    outputs = predict_fn(req.inputs)

                if not isinstance(outputs, dict):
                    outputs = {"prediction": outputs}

                latency = (time.monotonic() - start) * 1000
                results.append(InferenceResult(
                    request_id=req.request_id,
                    outputs=outputs,
                    latency_ms=latency,
                    finish_reason="stop",
                ))

            except Exception as exc:
                latency = (time.monotonic() - start) * 1000
                results.append(InferenceResult(
                    request_id=req.request_id,
                    outputs={"error": str(exc)},
                    latency_ms=latency,
                    finish_reason="error",
                    metadata={"error_type": type(exc).__name__},
                ))

        return results

    async def health(self) -> dict:
        return {"status": self._state.value}

    async def metrics(self) -> dict:
        return {"state": float(self._state == ModelState.LOADED)}

    async def memory_info(self) -> dict:
        return {"state": self._state.value}
