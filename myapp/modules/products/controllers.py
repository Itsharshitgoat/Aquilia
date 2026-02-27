"""
Products module controllers (request handlers).

This file defines the HTTP endpoints for the products module
using the modern Controller architecture with pattern-based routing.
"""

from aquilia import Controller, GET, POST, PUT, DELETE, RequestCtx, Response
from .faults import ProductsNotFoundFault
from .services import ProductsService


class ProductsController(Controller):
    """
    Controller for products endpoints.

    Provides RESTful CRUD operations for products.
    """
    prefix = "/"
    tags = ["products"]

    def __init__(self, service: "ProductsService" = None):
        # Instantiate service directly if not injected
        self.service = service or ProductsService()

    @GET("/")
    async def list_products(self, ctx: RequestCtx):
        """
        List all products.

        Example:
            GET /products/ -> {"items": [...], "total": 0}
        """
        items = await self.service.get_all()

        return Response.json({
            "items": items,
            "total": len(items)
        })

    @POST("/")
    async def create_product(self, ctx: RequestCtx):
        """
        Create a new product.

        Example:
            POST /products/
            Body: {"name": "Example"}
            -> {"id": 1, "name": "Example"}
        """
        data = await ctx.json()
        item = await self.service.create(data)
        return Response.json(item, status=201)

    @GET("/<id:int>")
    async def get_product(self, ctx: RequestCtx, id: int):
        """
        Get a product by ID.

        Example:
            GET /products/1 -> {"id": 1, "name": "Example"}
        """
        item = await self.service.get_by_id(id)
        if not item:
            raise ProductsNotFoundFault(item_id=id)

        return Response.json(item)

    @PUT("/<id:int>")
    async def update_product(self, ctx: RequestCtx, id: int):
        """
        Update a product by ID.

        Example:
            PUT /products/1
            Body: {"name": "Updated"}
            -> {"id": 1, "name": "Updated"}
        """
        data = await ctx.json()
        item = await self.service.update(id, data)
        if not item:
            raise ProductsNotFoundFault(item_id=id)

        return Response.json(item)

    @DELETE("/<id:int>")
    async def delete_product(self, ctx: RequestCtx, id: int):
        """
        Delete a product by ID.

        Example:
            DELETE /products/1 -> 204 No Content
        """
        deleted = await self.service.delete(id)
        if not deleted:
            raise ProductsNotFoundFault(item_id=id)

        return Response(status=204)