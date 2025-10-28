"""GraphQL router for FastAPI integration"""

from fastapi import Depends, Request
from typing import List, Optional

import strawberry
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.fastapi import GraphQLRouter
from strawberry.types import Info

from app.auth.router import get_current_user_optional
from app.auth.schemas import User as UserSchema
from app.database import get_db
from app.services.contact_service import ContactService
from app.services.product_service import ProductService


@strawberry.type
class Contact:
    """GraphQL Contact type"""

    id: int
    name: str
    email: Optional[str]
    phone: Optional[str]
    street: Optional[str]
    city: Optional[str]
    odoo_id: Optional[int]
    created_at: str
    updated_at: str


@strawberry.type
class Product:
    """GraphQL Product type"""

    id: int
    name: str
    default_code: Optional[str]
    list_price: Optional[float]
    standard_price: Optional[float]
    type: str
    odoo_id: Optional[int]
    created_at: str
    updated_at: str


@strawberry.type
class SyncResponse:
    """GraphQL Sync Response type"""

    success: bool
    message: str
    odoo_id: Optional[int]
    local_id: Optional[int]
    errors: List[str]


@strawberry.input
class ContactInput:
    """GraphQL Contact Input type"""

    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None


@strawberry.input
class ProductInput:
    """GraphQL Product Input type"""

    name: str
    default_code: Optional[str] = None
    list_price: Optional[float] = None
    standard_price: Optional[float] = None
    type: str = "product"


@strawberry.type
class Query:
    """GraphQL Query type"""

    @strawberry.field
    async def contacts(
        self, info: Info, skip: int = 0, limit: int = 100, search: Optional[str] = None
    ) -> List[Contact]:
        """Get contacts with pagination and search"""
        db: AsyncSession = info.context["db"]
        current_user: UserSchema = info.context["current_user"]

        # Check if user is authenticated
        if not current_user:
            return []

        service = ContactService(db, current_user)
        contacts = await service.get_contacts(skip=skip, limit=limit, search=search)

        return [
            Contact(
                id=contact.id,
                name=contact.name,
                email=contact.email,
                phone=contact.phone,
                street=contact.street,
                city=contact.city,
                odoo_id=contact.odoo_id,
                created_at=contact.created_at.isoformat(),
                updated_at=contact.updated_at.isoformat(),
            )
            for contact in contacts
        ]

    @strawberry.field
    async def contact(self, info: Info, id: int) -> Optional[Contact]:
        """Get specific contact by ID"""
        db: AsyncSession = info.context["db"]
        current_user: UserSchema = info.context["current_user"]

        # Check if user is authenticated
        if not current_user:
            return None

        service = ContactService(db, current_user)
        contact = await service.get_contact(id)

        if contact:
            return Contact(
                id=contact.id,
                name=contact.name,
                email=contact.email,
                phone=contact.phone,
                street=contact.street,
                city=contact.city,
                odoo_id=contact.odoo_id,
                created_at=contact.created_at.isoformat(),
                updated_at=contact.updated_at.isoformat(),
            )
        return None

    @strawberry.field
    async def products(
        self, info: Info, skip: int = 0, limit: int = 100, search: Optional[str] = None
    ) -> List[Product]:
        """Get products with pagination and search"""
        db: AsyncSession = info.context["db"]
        current_user: UserSchema = info.context["current_user"]

        # Check if user is authenticated
        if not current_user:
            return []

        service = ProductService(db, current_user)
        products = await service.get_products(skip=skip, limit=limit, search=search)

        return [
            Product(
                id=product.id,
                name=product.name,
                default_code=product.default_code,
                list_price=float(product.list_price) if product.list_price else None,
                standard_price=(
                    float(product.standard_price) if product.standard_price else None
                ),
                type=product.type,
                odoo_id=product.odoo_id,
                created_at=product.created_at.isoformat(),
                updated_at=product.updated_at.isoformat(),
            )
            for product in products
        ]

    @strawberry.field
    async def product(self, info: Info, id: int) -> Optional[Product]:
        """Get specific product by ID"""
        db: AsyncSession = info.context["db"]
        current_user: UserSchema = info.context["current_user"]

        # Check if user is authenticated
        if not current_user:
            return None

        service = ProductService(db, current_user)
        product = await service.get_product(id)

        if product:
            return Product(
                id=product.id,
                name=product.name,
                default_code=product.default_code,
                list_price=float(product.list_price) if product.list_price else None,
                standard_price=(
                    float(product.standard_price) if product.standard_price else None
                ),
                type=product.type,
                odoo_id=product.odoo_id,
                created_at=product.created_at.isoformat(),
                updated_at=product.updated_at.isoformat(),
            )
        return None


@strawberry.type
class Mutation:
    """GraphQL Mutation type"""

    @strawberry.mutation
    async def create_contact(self, info: Info, contact: ContactInput) -> SyncResponse:
        """Create a new contact"""
        db: AsyncSession = info.context["db"]
        current_user: UserSchema = info.context["current_user"]

        # Check if user is authenticated
        if not current_user:
            return SyncResponse(
                success=False,
                message="Authentication required",
                odoo_id=None,
                local_id=None,
                errors=["User must be authenticated to create contacts"]
            )

        service = ContactService(db, current_user)
        result = await service.create_contact(contact.__dict__)

        return SyncResponse(
            success=result.success,
            message=result.message,
            odoo_id=result.odoo_id,
            local_id=result.local_id,
            errors=result.errors,
        )

    @strawberry.mutation
    async def create_product(self, info: Info, product: ProductInput) -> SyncResponse:
        """Create a new product"""
        db: AsyncSession = info.context["db"]
        current_user: UserSchema = info.context["current_user"]

        # Check if user is authenticated
        if not current_user:
            return SyncResponse(
                success=False,
                message="Authentication required",
                odoo_id=None,
                local_id=None,
                errors=["User must be authenticated to create products"]
            )

        service = ProductService(db, current_user)
        result = await service.create_product(product.__dict__)

        return SyncResponse(
            success=result.success,
            message=result.message,
            odoo_id=result.odoo_id,
            local_id=result.local_id,
            errors=result.errors,
        )

    @strawberry.mutation
    async def sync_contacts_from_odoo(self, info: Info) -> SyncResponse:
        """Sync contacts from Odoo"""
        print("currency user : ", info.context)
        db: AsyncSession = info.context["db"]
        current_user: UserSchema = info.context["current_user"]

        # Check if user is authenticated
        if not current_user:
            return SyncResponse(
                success=False,
                message="Authentication required",
                odoo_id=None,
                local_id=None,
                errors=["User must be authenticated to sync contacts"]
            )

        service = ContactService(db, current_user)
        print("Service : ", service)
        result = await service.sync_contacts_from_odoo()

        return SyncResponse(
            success=result.success,
            message=result.message,
            odoo_id=result.odoo_id,
            local_id=result.local_id,
            errors=result.errors,
        )

    @strawberry.mutation
    async def sync_products_from_odoo(self, info: Info) -> SyncResponse:
        """Sync products from Odoo"""
        db: AsyncSession = info.context["db"]
        current_user: UserSchema = info.context["current_user"]

        # Check if user is authenticated
        if not current_user:
            return SyncResponse(
                success=False,
                message="Authentication required",
                odoo_id=None,
                local_id=None,
                errors=["User must be authenticated to sync products"]
            )

        service = ProductService(db, current_user)
        result = await service.sync_products_from_odoo()

        return SyncResponse(
            success=result.success,
            message=result.message,
            odoo_id=result.odoo_id,
            local_id=result.local_id,
            errors=result.errors,
        )


# Create GraphQL schema
schema = strawberry.Schema(query=Query, mutation=Mutation)


# Dependency context for GraphQL with optional authentication
async def get_graphql_context(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get context for GraphQL operations with optional authentication"""
    # Try to get current user from token, but don't require it
    current_user = await get_current_user_optional(request)
    
    return {"db": db, "current_user": current_user}


# Create GraphQL router with optional authentication
router = GraphQLRouter(
    schema,
    context_getter=get_graphql_context,
    graphiql=True
)
