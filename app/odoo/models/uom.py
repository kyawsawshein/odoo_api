"""Odoo XML-RPC client for FastAPI integration"""

from typing import Any, Dict, List, Optional
from ..datamodels.odoo_data import UomData
from ..client import OdooClient


class Uom(OdooClient):
    """Async Odoo XML-RPC client"""

    async def search_uom(self, domain: List = None) -> List[Dict]:
        """Search contacts with domain and fields"""
        if domain is None:
            domain = []
        fields = list(UomData.model_fields.keys())
        results = await self.execute_kw(
            "uom.uom", "search_read", [domain], {"fields": fields}
        )
        return [UomData.model_validate(res) for res in results]
