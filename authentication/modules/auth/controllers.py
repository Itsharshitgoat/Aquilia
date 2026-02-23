"""
Auth module controllers (request handlers).

This file defines the HTTP endpoints for the auth module
using the modern Controller architecture with pattern-based routing.
"""

from aquilia import Controller, GET, POST, PUT, DELETE, RequestCtx, Response
from .faults import AuthNotFoundFault
from .services import AuthService


from .blueprints import RegisterInputBlueprint, UserOutputBlueprint, LoginInputBlueprint


class AuthController(Controller):
    prefix = "/"
    tags = ["auth"]

    def __init__(self, service: AuthService):
        self.service = service

    @GET("/<name:str>")
    async def list_auth(self, name: str):
        return Response.json({"name": name })

    @POST("/register")
    async def create_auth(self, ctx: RequestCtx, data: RegisterInputBlueprint):
        user = await self.service.register(data=data)
        return Response.json(UserOutputBlueprint(instance=user).data, status=201)

    @POST("/login")
    async def login(self, ctx: RequestCtx, data: LoginInputBlueprint):
        resp = await self.service.login(data.email, data.password)
        return Response.json(resp, status=200)
 