"""
Auth module controller.
"""

from aquilia import Controller, GET, RequestCtx, Response


class AuthController(Controller):
    """Auth endpoints."""

    prefix = "/"
    tags = ["auth"]

    @GET("/")
    async def index(self, ctx: RequestCtx):
        return Response.json({"module": "auth", "status": "ok"})