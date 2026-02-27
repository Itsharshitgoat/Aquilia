"""
Users module controllers (request handlers).

This file defines the HTTP endpoints for the users module
using the modern Controller architecture with pattern-based routing.
"""

from aquilia import Controller, GET, POST, PUT, DELETE, RequestCtx, Response
from .faults import UsersNotFoundFault
from .services import UsersService


class UsersController(Controller):
    """
    Controller for users endpoints.

    Provides RESTful CRUD operations for users.
    """
    prefix = "/"
    tags = ["users"]

    def __init__(self, service: "UsersService" = None):
        # Instantiate service directly if not injected
        self.service = service or UsersService()

    @GET("/")
    async def list_users(self, ctx: RequestCtx):
        """
        List all users.

        Example:
            GET /users/ -> {"items": [...], "total": 0}
        """
        items = await self.service.get_all()

        return Response.json({
            "items": items,
            "total": len(items)
        })

    @POST("/")
    async def create_user(self, ctx: RequestCtx):
        """
        Create a new user.

        Example:
            POST /users/
            Body: {"name": "Example"}
            -> {"id": 1, "name": "Example"}
        """
        data = await ctx.json()
        item = await self.service.create(data)
        return Response.json(item, status=201)

    @GET("/<id:int>")
    async def get_user(self, ctx: RequestCtx, id: int):
        """
        Get a user by ID.

        Example:
            GET /users/1 -> {"id": 1, "name": "Example"}
        """
        item = await self.service.get_by_id(id)
        if not item:
            raise UsersNotFoundFault(item_id=id)

        return Response.json(item)

    @PUT("/<id:int>")
    async def update_user(self, ctx: RequestCtx, id: int):
        """
        Update a user by ID.

        Example:
            PUT /users/1
            Body: {"name": "Updated"}
            -> {"id": 1, "name": "Updated"}
        """
        data = await ctx.json()
        item = await self.service.update(id, data)
        if not item:
            raise UsersNotFoundFault(item_id=id)

        return Response.json(item)

    @DELETE("/<id:int>")
    async def delete_user(self, ctx: RequestCtx, id: int):
        """
        Delete a user by ID.

        Example:
            DELETE /users/1 -> 204 No Content
        """
        deleted = await self.service.delete(id)
        if not deleted:
            raise UsersNotFoundFault(item_id=id)

        return Response(status=204)