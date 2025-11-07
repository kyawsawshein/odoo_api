"""Odoo XML-RPC client for FastAPI integration"""

import xmlrpc.client
from typing import Any, Dict, List, Optional

# import aiohttp
# import asyncio
from urllib.parse import urljoin

from app.config import settings

from .datamodels.odoo_data import ContactData, ProductData, UomData, CategoryData, CurrencyData

class OdooClient:
    """Async Odoo XML-RPC client"""

    def __init__(self, url: str, db: str, username: str, password: str, uid: Optional[int] = None):
        self.url = url
        self.db = db
        self.username = username
        self.password = password
        self.uid = uid

        # Create XML-RPC clients
        self.common = xmlrpc.client.ServerProxy(urljoin(url, "/xmlrpc/2/common"))
        self.models = xmlrpc.client.ServerProxy(urljoin(url, "/xmlrpc/2/object"))

    async def authenticate(self) -> Optional[int]:
        """Authenticate with Odoo and return user ID"""
        try:
            self.uid = self.common.authenticate(
                self.db, self.username, self.password, {}
            )
            if not self.uid:
                raise Exception("Invalid credentials or database name")

            return self.uid
        except Exception as e:
            raise Exception(f"Odoo authentication failed: {str(e)}")

    async def execute_kw(
        self, model: str, method: str, args: List, kwargs: Dict = None
    ) -> Any:
        """Execute Odoo method with arguments"""
        if not self.uid:
            await self.authenticate()

        if kwargs is None:
            kwargs = {}

        try:
            return self.models.execute_kw(
                self.db, self.uid, self.password, model, method, args, kwargs
            )
        except Exception as e:
            raise Exception(f"Odoo operation failed: {str(e)}")

    # Projecet Operations
    async def create_project(self, project_data: Dict) -> int:
        """Create a new contact in Odoo"""
        return await self.execute_kw("project.project", "create", [project_data])

    async def update_project(self, project_id: int, project_data: Dict) -> bool:
        """Update existing contact"""
        return await self.execute_kw("project.project", "write", [[project_id], project_data])

    # Contact Operations
    async def create_contact(self, contact_data: Dict) -> int:
        """Create a new contact in Odoo"""
        return await self.execute_kw("res.partner", "create", [contact_data])

    async def update_contact(self, contact_id: int, contact_data: Dict) -> bool:
        """Update existing contact"""
        return await self.execute_kw(
            "res.partner", "write", [[contact_id], contact_data]
        )

    async def search_contacts(
        self, domain: List = None, fields: List = None
    ) -> List[Dict]:
        """Search contacts with domain and fields"""
        if domain is None:
            domain = []
        if fields is None:
            fields = list(ContactData.model_fields.keys())
        results = await self.execute_kw(
            "res.partner", "search_read", [domain], {"fields": fields}
        )
        return [ContactData.model_validate(res) for res in results]

    # Product Operations
    async def create_product(self, product_data: Dict) -> int:
        """Create a new product in Odoo"""
        return await self.execute_kw("product.product", "create", [product_data])

    async def update_product(self, product_id: int, product_data: Dict) -> bool:
        """Update existing product"""
        return await self.execute_kw(
            "product.product", "write", [[product_id], product_data]
        )

    async def search_products(
        self, domain: List = None, fields: List = None
    ) -> List[Dict]:
        """Search products with domain and fields"""
        if domain is None:
            domain = []
        if fields is None:
            fields = list(ProductData.model_fields.keys())

        results = await self.execute_kw(
            "product.product", "search_read", [domain], {"fields": fields}
        )
        return [ProductData.model_validate(res) for res in results]

    # Inventory Operations
    async def get_stock_quantities(self, product_ids: List[int] = None) -> List[Dict]:
        """Get stock quantities for products"""
        domain = []
        if product_ids:
            domain = [("product_id", "in", product_ids)]

        return await self.execute_kw(
            "stock.quant",
            "search_read",
            [domain],
            {"fields": ["product_id", "quantity", "location_id"]},
        )

    async def update_inventory(self, inventory_data: Dict) -> int:
        """Create inventory adjustment"""
        return await self.execute_kw("stock.inventory", "create", [inventory_data])

    async def create_inventory_line(self, line_data: Dict) -> int:
        """Create inventory adjustment line"""
        return await self.execute_kw("stock.inventory.line", "create", [line_data])

    # Purchase Operations
    async def create_purchase_order(self, order_data: Dict) -> int:
        """Create a new purchase order"""
        return await self.execute_kw("purchase.order", "create", [order_data])

    async def create_purchase_order_line(self, line_data: Dict) -> int:
        """Create purchase order line"""
        return await self.execute_kw("purchase.order.line", "create", [line_data])

    async def confirm_purchase_order(self, order_id: int) -> bool:
        """Confirm purchase order"""
        return await self.execute_kw("purchase.order", "button_confirm", [[order_id]])

    # Sale Operations
    async def create_sale_order(self, order_data: Dict) -> int:
        """Create a new sale order"""
        return await self.execute_kw("sale.order", "create", [order_data])

    async def create_sale_order_line(self, line_data: Dict) -> int:
        """Create sale order line"""
        return await self.execute_kw("sale.order.line", "create", [line_data])

    async def confirm_sale_order(self, order_id: int) -> bool:
        """Confirm sale order"""
        return await self.execute_kw("sale.order", "action_confirm", [[order_id]])

    # Delivery Operations
    async def create_delivery(self, delivery_data: Dict) -> int:
        """Create delivery order"""
        return await self.execute_kw("stock.picking", "create", [delivery_data])

    async def confirm_delivery(self, delivery_id: int) -> bool:
        """Confirm delivery"""
        return await self.execute_kw("stock.picking", "action_confirm", [[delivery_id]])

    async def validate_delivery(self, delivery_id: int) -> bool:
        """Validate delivery"""
        return await self.execute_kw(
            "stock.picking", "button_validate", [[delivery_id]]
        )

    # Accounting Operations
    async def create_account_move(self, move_data: Dict) -> int:
        """Create accounting journal entry"""
        return await self.execute_kw("account.move", "create", [move_data])

    async def create_account_move_line(self, line_data: Dict) -> int:
        """Create journal entry line"""
        return await self.execute_kw("account.move.line", "create", [line_data])

    async def post_account_move(self, move_id: int) -> bool:
        """Post accounting journal entry"""
        return await self.execute_kw("account.move", "action_post", [[move_id]])

    # Generic Operations
    async def search_records(
        self, model: str, domain: List = None, fields: List = None, limit: int = None, offset: int = None
    ) -> List[Dict]:
        """Generic search records from any model"""
        if domain is None:
            domain = []
        if fields is None:
            fields = ["id", "name"]

        kwargs = {"fields": fields}
        if limit:
            kwargs["limit"] = limit
        if offset:
            kwargs["offset"] = offset

        return await self.execute_kw(model, "search_read", [domain], kwargs)

    async def read_records(
        self, model: str, record_ids: List[int], fields: List = None
    ) -> List[Dict]:
        """Read multiple records by IDs"""
        if fields is None:
            fields = ["id", "name"]
        return await self.execute_kw(
            model, "read", [record_ids], {"fields": fields}
        )

    async def create_record(self, model: str, values: Dict) -> int:
        """Create a new record in any model"""
        for value in values:
            print(type(value))
        return await self.execute_kw(model, "create", [values])

    async def update_record(self, model: str, record_id: int, values: Dict) -> bool:
        """Update existing record in any model"""
        return await self.execute_kw(model, "write", [[record_id], values])

    async def read_record(
        self, model: str, record_id: int, fields: List = None
    ) -> Dict:
        """Read specific record"""
        if fields is None:
            fields = ["id", "name"]

        records = await self.execute_kw(
            model, "read", [[record_id]], {"fields": fields}
        )
        return records[0] if records else {}

    async def delete_record(self, model: str, record_id: int) -> bool:
        """Delete record"""
        return await self.execute_kw(model, "unlink", [[record_id]])


class OdooClientPool:
    """Pool of Odoo clients for concurrent operations"""

    def __init__(self):
        self.clients = {}

    async def get_client(
        self, url: str, db: str, username: str, password: str, uid: Optional[int] = None
    ) -> OdooClient:
        """Get or create Odoo client from pool"""
        key = f"{db}:{username}"

        if key not in self.clients:
            print("#=================== Odoo authenticate ==========================")
            client = OdooClient(url or settings.ODOO_URL, db, username, password, uid)
            if not uid:
                await client.authenticate()
            self.clients[key] = client

        return self.clients[key]

    async def get_client_by_uid(self, uid: int) -> Optional[OdooClient]:
        """Get Odoo client by user ID from pool"""
        for client in self.clients.values():
            if client.uid == uid:
                return client
        return None

    async def close_all(self):
        """Close all clients in pool"""
        self.clients.clear()


class SessionOdooClient:
    """Session-based Odoo client that uses cookies for authentication"""
    
    def __init__(self):
        self.pool = OdooClientPool()
    
    async def authenticate_and_get_uid(
        self, url: str, db: str, username: str, password: str
    ) -> int:
        """Authenticate with Odoo and return user ID for session storage"""
        client = await self.pool.get_client(url, db, username, password)
        return client.uid
    
    async def execute_with_session(
        self,
        url: str,
        db: str,
        username: str,
        password: str,
        uid: Optional[int],
        model: str,
        method: str,
        args: List,
        kwargs: Dict = None
    ) -> Any:
        """Execute Odoo method using session (uid from cookie) if available"""
        if uid:
            # Try to use existing session
            client = await self.pool.get_client(url, db, username, password, uid)
            try:
                return await client.execute_kw(model, method, args, kwargs)
            except Exception:
                # If session is invalid, re-authenticate
                print("Session invalid, re-authenticating...")
                client = await self.pool.get_client(url, db, username, password)
                return await client.execute_kw(model, method, args, kwargs)
        else:
            # No session, authenticate first
            client = await self.pool.get_client(url, db, username, password)
            return await client.execute_kw(model, method, args, kwargs)


# Global Odoo client pool
odoo_pool = OdooClientPool()
session_odoo_client = SessionOdooClient()
