"""
AquilAdmin — AdminSite (Central Registry).

The AdminSite is the central coordination point for the admin system.
It manages:
- Model registration (explicit + auto-discovered)
- Dashboard data aggregation
- Audit log
- Template rendering integration
- Permission checks

Design: Singleton pattern with lazy initialization.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from aquilia.models.base import Model
    from aquilia.auth.core import Identity

from .options import ModelAdmin
from .permissions import AdminRole, AdminPermission, get_admin_role, has_admin_permission, has_model_permission
from .audit import AdminAuditLog, AdminAction
from .faults import (
    AdminAuthorizationFault,
    AdminModelNotFoundFault,
    AdminRecordNotFoundFault,
    AdminValidationFault,
)

logger = logging.getLogger("aquilia.admin.site")


class AdminSite:
    """
    Central admin site — manages all registered models.

    Singleton-safe with a default() class method.
    Multiple AdminSite instances can coexist for multi-tenant scenarios.

    Attributes:
        name: Site identifier (default "admin")
        title: Dashboard title
        header: Header text
        url_prefix: URL prefix (default "/admin")
        login_url: Login page URL
    """

    _default_instance: Optional[AdminSite] = None

    def __init__(
        self,
        name: str = "admin",
        *,
        title: str = "Aquilia Admin",
        header: str = "Aquilia Administration",
        url_prefix: str = "/admin",
        login_url: str = "/admin/login",
    ):
        self.name = name
        self.title = title
        self.header = header
        self.url_prefix = url_prefix.rstrip("/")
        self.login_url = login_url

        # Registry: model_class -> ModelAdmin instance
        self._registry: Dict[Type[Model], ModelAdmin] = {}

        # Audit log
        self.audit_log = AdminAuditLog()

        # Initialization state
        self._initialized = False

    @classmethod
    def default(cls) -> AdminSite:
        """Get or create the default AdminSite singleton."""
        if cls._default_instance is None:
            cls._default_instance = cls()
        return cls._default_instance

    @classmethod
    def reset(cls) -> None:
        """Reset the default site (for testing)."""
        cls._default_instance = None

    def initialize(self) -> None:
        """
        Initialize the admin site.

        Flushes pending registrations and runs autodiscovery.
        Called during app startup.
        """
        if self._initialized:
            return

        from .registry import flush_pending_registrations, autodiscover

        # Flush any @register decorators that fired before init
        flushed = flush_pending_registrations()
        if flushed:
            logger.debug("Flushed %d pending admin registrations", flushed)

        # Auto-discover remaining models
        auto = autodiscover()
        if auto:
            logger.debug("Auto-discovered %d models for admin", len(auto))

        self._initialized = True
        logger.info(
            "AdminSite '%s' initialized with %d models",
            self.name,
            len(self._registry),
        )

    # ── Registration ─────────────────────────────────────────────────

    def register_admin(self, model_cls: Type[Model], admin: ModelAdmin) -> None:
        """Register a model with its ModelAdmin configuration."""
        admin.model = model_cls
        self._registry[model_cls] = admin
        logger.debug("Registered admin for %s", model_cls.__name__)

    def register(self, model_cls: Type[Model], admin_class: Optional[Type[ModelAdmin]] = None) -> None:
        """
        Register a model (convenience method).

        If admin_class is None, uses default ModelAdmin.
        """
        if admin_class is None:
            admin_class = ModelAdmin
        admin = admin_class(model=model_cls)
        self.register_admin(model_cls, admin)

    def unregister(self, model_cls: Type[Model]) -> None:
        """Unregister a model."""
        self._registry.pop(model_cls, None)

    def is_registered(self, model_cls: Type[Model]) -> bool:
        """Check if a model is registered."""
        return model_cls in self._registry

    # ── Registry access ──────────────────────────────────────────────

    def get_model_admin(self, model_cls_or_name: Any) -> ModelAdmin:
        """
        Get ModelAdmin for a model class or name.

        Raises AdminModelNotFoundFault if not found.
        """
        if isinstance(model_cls_or_name, str):
            for cls, admin in self._registry.items():
                if cls.__name__.lower() == model_cls_or_name.lower():
                    return admin
            raise AdminModelNotFoundFault(model_cls_or_name)
        else:
            admin = self._registry.get(model_cls_or_name)
            if admin is None:
                raise AdminModelNotFoundFault(
                    model_cls_or_name.__name__ if hasattr(model_cls_or_name, "__name__") else str(model_cls_or_name)
                )
            return admin

    def get_model_class(self, model_name: str) -> Type[Model]:
        """
        Get model class by name.

        Raises AdminModelNotFoundFault if not found.
        """
        for cls in self._registry:
            if cls.__name__.lower() == model_name.lower():
                return cls
        raise AdminModelNotFoundFault(model_name)

    def get_app_list(self, identity: Optional[Identity] = None) -> List[Dict[str, Any]]:
        """
        Get list of admin apps/models grouped by app_label.

        Filters by identity permissions.
        Returns list of app dicts with their models.
        """
        apps: Dict[str, Dict[str, Any]] = {}

        for model_cls, admin in self._registry.items():
            # Permission check
            if identity and not admin.has_module_permission(identity):
                continue

            app_label = admin.get_app_label()
            if app_label not in apps:
                apps[app_label] = {
                    "app_label": app_label,
                    "app_name": app_label.replace("_", " ").title(),
                    "models": [],
                }

            apps[app_label]["models"].append({
                "name": admin.get_model_name(),
                "name_plural": admin.get_model_name_plural(),
                "model_name": model_cls.__name__,
                "url_name": model_cls.__name__.lower(),
                "icon": admin.icon,
                "perms": {
                    "view": admin.has_view_permission(identity),
                    "add": admin.has_add_permission(identity),
                    "change": admin.has_change_permission(identity),
                    "delete": admin.has_delete_permission(identity),
                },
            })

        return sorted(apps.values(), key=lambda a: a["app_label"])

    def get_registered_models(self) -> Dict[str, ModelAdmin]:
        """Get all registered model name -> ModelAdmin pairs."""
        return {cls.__name__: admin for cls, admin in self._registry.items()}

    # ── Dashboard data ───────────────────────────────────────────────

    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """
        Aggregate dashboard statistics.

        Returns model counts and recent audit entries.
        """
        stats: Dict[str, Any] = {
            "total_models": len(self._registry),
            "model_counts": {},
            "recent_actions": [],
        }

        # Count records per model (best effort)
        for model_cls, admin in self._registry.items():
            try:
                count = await model_cls.objects.count()
                stats["model_counts"][model_cls.__name__] = count
            except Exception:
                stats["model_counts"][model_cls.__name__] = "?"

        # Recent audit entries
        stats["recent_actions"] = [
            e.to_dict() for e in self.audit_log.get_entries(limit=10)
        ]

        return stats

    # ── CRUD operations ──────────────────────────────────────────────

    async def list_records(
        self,
        model_name: str,
        *,
        page: int = 1,
        per_page: int = 25,
        search: str = "",
        filters: Optional[Dict[str, Any]] = None,
        ordering: Optional[str] = None,
        identity: Optional[Identity] = None,
    ) -> Dict[str, Any]:
        """
        List records for a model with pagination, search, and filtering.

        Returns dict with records, total count, and pagination info.
        """
        model_cls = self.get_model_class(model_name)
        admin = self.get_model_admin(model_cls)

        # Permission check
        if identity and not admin.has_view_permission(identity):
            raise AdminAuthorizationFault(action="view", resource=model_name)

        # Build queryset
        qs = model_cls.objects.get_queryset()

        # Apply search
        if search and admin.get_search_fields():
            # Build OR search across search fields
            search_q = None
            for field_name in admin.get_search_fields():
                from aquilia.models.query import QNode
                q = QNode(**{f"{field_name}__icontains": search})
                if search_q is None:
                    search_q = q
                else:
                    search_q = search_q | q
            if search_q:
                qs = qs.apply_q(search_q)

        # Apply filters
        if filters:
            qs = qs.filter(**filters)

        # Apply ordering
        if ordering:
            qs = qs.order(ordering)
        else:
            default_ordering = admin.get_ordering()
            if default_ordering:
                qs = qs.order(*default_ordering)

        # Get total count
        total = await qs.count()

        # Apply pagination
        offset = (page - 1) * per_page
        records = await qs.limit(per_page).offset(offset).all()

        # Format records for display
        list_display = admin.get_list_display()
        rows = []
        for record in records:
            row = {"pk": record.pk}
            for field_name in list_display:
                value = getattr(record, field_name, None)
                row[field_name] = admin.format_value(field_name, value)
                row[f"_raw_{field_name}"] = value
            rows.append(row)

        # Pagination info
        total_pages = max(1, (total + per_page - 1) // per_page)

        return {
            "rows": rows,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "list_display": list_display,
            "list_filter": admin.get_list_filter(),
            "search_fields": admin.get_search_fields(),
            "ordering": ordering,
            "search": search,
            "model_name": model_cls.__name__,
            "verbose_name": admin.get_model_name(),
            "verbose_name_plural": admin.get_model_name_plural(),
        }

    async def get_record(
        self,
        model_name: str,
        pk: Any,
        *,
        identity: Optional[Identity] = None,
    ) -> Dict[str, Any]:
        """
        Get a single record with field metadata for the edit form.
        """
        model_cls = self.get_model_class(model_name)
        admin = self.get_model_admin(model_cls)

        if identity and not admin.has_view_permission(identity):
            raise AdminAuthorizationFault(action="view", resource=model_name)

        record = await model_cls.get(pk=pk)
        if record is None:
            raise AdminRecordNotFoundFault(model_name, str(pk))

        # Build field data
        fields_data = []
        readonly = admin.get_readonly_fields()
        for field_name in admin.get_fields():
            meta = admin.get_field_metadata(field_name)
            meta["value"] = getattr(record, field_name, None)
            meta["readonly"] = field_name in readonly
            fields_data.append(meta)

        # Also include readonly fields that aren't in get_fields
        for field_name in readonly:
            if field_name not in [f["name"] for f in fields_data]:
                meta = admin.get_field_metadata(field_name)
                meta["value"] = getattr(record, field_name, None)
                meta["readonly"] = True
                fields_data.append(meta)

        return {
            "pk": record.pk,
            "record": record,
            "fields": fields_data,
            "fieldsets": admin.get_fieldsets(),
            "model_name": model_cls.__name__,
            "verbose_name": admin.get_model_name(),
            "can_change": admin.has_change_permission(identity),
            "can_delete": admin.has_delete_permission(identity),
        }

    async def create_record(
        self,
        model_name: str,
        data: Dict[str, Any],
        *,
        identity: Optional[Identity] = None,
    ) -> Any:
        """Create a new record."""
        model_cls = self.get_model_class(model_name)
        admin = self.get_model_admin(model_cls)

        if identity and not admin.has_add_permission(identity):
            raise AdminAuthorizationFault(action="add", resource=model_name)

        # Filter to editable fields only
        editable = set(admin.get_fields()) - set(admin.get_readonly_fields())
        clean_data = {k: v for k, v in data.items() if k in editable}

        try:
            record = await model_cls.create(**clean_data)
        except Exception as e:
            raise AdminValidationFault(str(e))

        # Audit log
        if identity:
            self.audit_log.log(
                user_id=identity.id,
                username=identity.get_attribute("name", identity.id),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.CREATE,
                model_name=model_name,
                record_pk=str(record.pk),
                changes=clean_data,
            )

        return record

    async def update_record(
        self,
        model_name: str,
        pk: Any,
        data: Dict[str, Any],
        *,
        identity: Optional[Identity] = None,
    ) -> Any:
        """Update an existing record."""
        model_cls = self.get_model_class(model_name)
        admin = self.get_model_admin(model_cls)

        if identity and not admin.has_change_permission(identity):
            raise AdminAuthorizationFault(action="change", resource=model_name)

        record = await model_cls.get(pk=pk)
        if record is None:
            raise AdminRecordNotFoundFault(model_name, str(pk))

        # Filter to editable fields and track changes
        editable = set(admin.get_fields()) - set(admin.get_readonly_fields())
        changes: Dict[str, Dict[str, Any]] = {}
        update_data: Dict[str, Any] = {}

        for field_name, new_value in data.items():
            if field_name not in editable:
                continue
            old_value = getattr(record, field_name, None)
            if str(old_value) != str(new_value):
                changes[field_name] = {"old": old_value, "new": new_value}
                update_data[field_name] = new_value

        if update_data:
            try:
                await model_cls.objects.filter(**{model_cls._pk_attr: pk}).update(update_data)
                # Refresh record
                record = await model_cls.get(pk=pk)
            except Exception as e:
                raise AdminValidationFault(str(e))

        # Audit log
        if identity and changes:
            self.audit_log.log(
                user_id=identity.id,
                username=identity.get_attribute("name", identity.id),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.UPDATE,
                model_name=model_name,
                record_pk=str(pk),
                changes=changes,
            )

        return record

    async def delete_record(
        self,
        model_name: str,
        pk: Any,
        *,
        identity: Optional[Identity] = None,
    ) -> bool:
        """Delete a record."""
        model_cls = self.get_model_class(model_name)
        admin = self.get_model_admin(model_cls)

        if identity and not admin.has_delete_permission(identity):
            raise AdminAuthorizationFault(action="delete", resource=model_name)

        record = await model_cls.get(pk=pk)
        if record is None:
            raise AdminRecordNotFoundFault(model_name, str(pk))

        try:
            await model_cls.objects.filter(**{model_cls._pk_attr: pk}).delete()
        except Exception as e:
            raise AdminValidationFault(str(e))

        # Audit log
        if identity:
            self.audit_log.log(
                user_id=identity.id,
                username=identity.get_attribute("name", identity.id),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.DELETE,
                model_name=model_name,
                record_pk=str(pk),
            )

        return True

    async def execute_action(
        self,
        model_name: str,
        action_name: str,
        selected_pks: List[Any],
        *,
        identity: Optional[Identity] = None,
    ) -> str:
        """
        Execute a bulk action on selected records.

        Returns a result message string.
        """
        model_cls = self.get_model_class(model_name)
        admin = self.get_model_admin(model_cls)

        if identity and not has_admin_permission(identity, AdminPermission.ACTION_EXECUTE):
            raise AdminAuthorizationFault(action="execute action", resource=model_name)

        actions = admin.get_actions()
        if action_name not in actions:
            from .faults import AdminActionFault
            raise AdminActionFault(action_name, "Action not found")

        action_desc = actions[action_name]

        # Build queryset for selected records
        qs = model_cls.objects.filter(**{f"{model_cls._pk_attr}__in": selected_pks})

        try:
            result = await action_desc.func(admin, None, qs)
        except Exception as e:
            from .faults import AdminActionFault
            raise AdminActionFault(action_name, str(e))

        # Audit log
        if identity:
            self.audit_log.log(
                user_id=identity.id,
                username=identity.get_attribute("name", identity.id),
                role=str(get_admin_role(identity) or "unknown"),
                action=AdminAction.BULK_ACTION,
                model_name=model_name,
                metadata={"action": action_name, "pks": [str(pk) for pk in selected_pks]},
            )

        return result or f"Action '{action_name}' executed on {len(selected_pks)} record(s)"
