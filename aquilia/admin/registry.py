"""
AquilAdmin — Model Registration & Auto-Discovery.

Provides the @register decorator and autodiscover() function for
registering models with the admin site.

Auto-discovery:
    When autodiscover() is called (typically at startup), it scans
    ModelRegistry.all_models() and registers any model that doesn't
    already have an explicit ModelAdmin with the default ModelAdmin.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from aquilia.models.base import Model
    from .options import ModelAdmin
    from .site import AdminSite

logger = logging.getLogger("aquilia.admin.registry")

# Pending registrations (before AdminSite is created)
_pending_registrations: List[tuple] = []


def register(
    model_or_admin: Any = None,
    *,
    site: Optional[AdminSite] = None,
) -> Callable:
    """
    Register a model or ModelAdmin with the admin site.

    Can be used as a class decorator or called directly.

    Usage (decorator on ModelAdmin):
        @register
        class UserAdmin(ModelAdmin):
            model = User
            list_display = ["id", "name", "email"]

    Usage (decorator with model):
        @register(User)
        class UserAdmin(ModelAdmin):
            list_display = ["id", "name"]

    Usage (direct call):
        register(User, UserAdmin)
    """
    from .options import ModelAdmin as _ModelAdmin

    def _do_register(admin_cls: Type[_ModelAdmin], model_cls: Optional[Type[Model]] = None):
        """Actually register the admin class."""
        actual_model = model_cls or admin_cls.model
        if actual_model is None:
            raise ValueError(
                f"ModelAdmin {admin_cls.__name__} must specify a model class "
                "either via the 'model' attribute or as a decorator argument."
            )

        admin_instance = admin_cls(model=actual_model)

        if site is not None:
            site.register_admin(actual_model, admin_instance)
        else:
            # Try default site
            from .site import AdminSite
            default_site = AdminSite.default()
            if default_site._initialized:
                default_site.register_admin(actual_model, admin_instance)
            else:
                _pending_registrations.append((actual_model, admin_instance))

    # Handle various calling patterns
    if model_or_admin is None:
        # @register or @register()
        def decorator(cls):
            _do_register(cls)
            return cls
        return decorator

    if isinstance(model_or_admin, type):
        from .options import ModelAdmin as _ModelAdmin
        if issubclass(model_or_admin, _ModelAdmin):
            # @register applied to ModelAdmin class
            _do_register(model_or_admin)
            return model_or_admin
        else:
            # @register(UserModel) — decorator factory
            def decorator(cls):
                _do_register(cls, model_or_admin)
                return cls
            return decorator

    raise TypeError(f"Invalid argument to @register: {model_or_admin!r}")


def autodiscover() -> Dict[str, Type[Model]]:
    """
    Auto-discover and register all models from ModelRegistry.

    Scans ModelRegistry.all_models() and registers any model that
    doesn't already have an explicit ModelAdmin with the default.

    Returns:
        Dictionary of model_name -> model_class that were auto-registered.
    """
    from .site import AdminSite
    from .options import ModelAdmin
    from aquilia.models.registry import ModelRegistry

    site = AdminSite.default()
    auto_registered: Dict[str, type] = {}

    all_models = ModelRegistry.all_models()
    for name, model_cls in all_models.items():
        # Skip abstract models
        if hasattr(model_cls, "_meta") and model_cls._meta.abstract:
            continue

        # Skip already registered
        if site.is_registered(model_cls):
            continue

        # Auto-register with default ModelAdmin
        admin_instance = ModelAdmin(model=model_cls)
        site.register_admin(model_cls, admin_instance)
        auto_registered[name] = model_cls
        logger.debug("Auto-registered model: %s", name)

    logger.info(
        "Admin autodiscover complete: %d models auto-registered, %d total",
        len(auto_registered),
        len(site._registry),
    )

    return auto_registered


def flush_pending_registrations() -> int:
    """
    Flush any pending registrations to the default AdminSite.

    Called during AdminSite initialization.
    Returns count of flushed registrations.
    """
    from .site import AdminSite

    site = AdminSite.default()
    count = 0

    for model_cls, admin_instance in _pending_registrations:
        site.register_admin(model_cls, admin_instance)
        count += 1

    _pending_registrations.clear()
    return count
