from aquilia.blueprints import Blueprint, EmailFacet, Field
from .models.models import UsersModel


class NameBlueprint(Blueprint):
    first_name: str
    last_name: str


class RegisterInputBlueprint(Blueprint):
    email: str = Field(max_length=225)
    password: str
    username: str = Field(required=False, default="unknown")
    name: NameBlueprint = Field(required=False)
    full_name: str = Field(required=False)


class LoginInputBlueprint(Blueprint):
    email: str
    password: str


class UserOutputBlueprint(Blueprint):
    name: NameBlueprint

    class Spec:
        model = UsersModel
        projections = {
            "default": "__all__"
        }
        read_only_fields = ["id", "created_at"]
        extra_kwargs = {
            "password": {"write_only": True}
        }
