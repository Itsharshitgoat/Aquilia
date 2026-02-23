"""
Auth module services (business logic).

Services contain the core business logic and are auto-wired
via dependency injection.
"""

from typing import Optional, List
from aquilia.di import service

from .blueprints import RegisterInputBlueprint
from .faults import AuthOperationFault
from .models.models import UsersModel
from aquilia.auth import (
    AuthManager,
    PasswordHasher, 
    Identity, 
    PasswordCredential, 
    IdentityType,
    IdentityStatus
)

@service(scope="app")
class AuthService:
    """
    Service for auth business logic.

    This service is automatically registered with the DI container
    and can be injected into controllers.

    To inject dependencies, add type-annotated parameters to __init__:

        def __init__(self, db: AquiliaDatabase, auth: AuthManager):
            self.db = db
            self.auth = auth
    """

    def __init__(self, auth: AuthManager, hasher: PasswordHasher):
        self.auth = auth
        self.hasher = hasher

    async def register(self, data: RegisterInputBlueprint):
        password_hash = self.hasher.hash(data.password)

        if await UsersModel.query().filter(email = data.email).exists():
            raise AuthOperationFault("user.register", f"Email: {data.email} already exisits!")
            
        username = data.username
        if username == "unknown":
            username = data.email.split("@")[0]
            
        name_dict = {"first_name": "Unknown", "last_name": "Unknown"}
        if getattr(data, "name", None):
            name_dict = {"first_name": data.name.first_name, "last_name": data.name.last_name}
        elif getattr(data, "full_name", None):
            parts = data.full_name.split(" ", 1)
            name_dict["first_name"] = parts[0]
            if len(parts) > 1:
                name_dict["last_name"] = parts[1]

        user = await UsersModel.create(
            username=username,
            email=data.email,
            password=password_hash,
            name=name_dict
        )
        identity = Identity(
            id = str(user.id),
            type = IdentityType.USER,
            status = IdentityStatus.ACTIVE,
            attributes = {
                "username": username,
                "email": data.email,
                "name": name_dict
            }
        )
        
        await self.auth.identity_store.create(identity = identity)

        credential = PasswordCredential(
            identity_id = str(user.id),
            password_hash = password_hash
        )

        await self.auth.credential_store.save_password(credential = credential)
        return user

    async def login(self, email: str, password: str) -> dict:
        auth_result = await self.auth.authenticate_password(
            username=email,
            password=password
        )
        return {
            "access_token": auth_result.access_token,
            "refresh_token": auth_result.refresh_token,
            "token_type": "Bearer",
            "expires_in": auth_result.expires_in
        }