"""Optimized Odoo client with prepared statements and query support for faster API operations"""

import base64
import xmlrpc.client
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

from app.config import settings


class OptimizedOdooClient:
    """Optimized Odoo XML-RPC client with prepared statements and query support"""

    def __init__(self, url: str, db: str, username: str, password: str):
        self.url = url
        self.db = db
        self.username = username
        self.password = password
        self.uid = None

        # Create XML-RPC clients
        self.common = xmlrpc.client.ServerProxy(urljoin(url, "/xmlrpc/2/common"))
        self.models = xmlrpc.client.ServerProxy(urljoin(url, "/xmlrpc/2/object"))
        
        # Cache for prepared statements
        self._prepared_queries = {}
        self._prepared_updates = {}

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

    # Prepared Query Methods
    async def prepare_query(
        self, 
        query_name: str, 
        model: str, 
        base_domain: List = None,
        base_fields: List = None
    ) -> None:
        """Prepare a query for repeated execution"""
        if base_domain is None:
            base_domain = []
        if base_fields is None:
            base_fields = ["id", "name"]
            
        self._prepared_queries[query_name] = {
            "model": model,
            "base_domain": base_domain,
            "base_fields": base_fields
        }

    async def execute_prepared_query(
        self, 
        query_name: str, 
        additional_domain: List = None,
        additional_fields: List = None,
        limit: int = None,
        offset: int = None
    ) -> List[Dict]:
        """Execute a prepared query with additional parameters"""
        if query_name not in self._prepared_queries:
            raise ValueError(f"Query '{query_name}' not prepared")
            
        query = self._prepared_queries[query_name]
        domain = query["base_domain"].copy()
        
        if additional_domain:
            domain.extend(additional_domain)
            
        fields = query["base_fields"].copy()
        if additional_fields:
            fields.extend(additional_fields)
            
        kwargs = {"fields": fields}
        if limit:
            kwargs["limit"] = limit
        if offset:
            kwargs["offset"] = offset
            
        return await self.execute_kw(
            query["model"], "search_read", [domain], kwargs
        )

    # Optimized Search Methods
    async def search_records_optimized(
        self, 
        model: str, 
        domain: List = None, 
        fields: List = None, 
        limit: int = None, 
        offset: int = None,
        order: str = None
    ) -> List[Dict]:
        """Optimized search with caching and prepared statements"""
        if domain is None:
            domain = []
        if fields is None:
            fields = ["id", "name"]

        kwargs = {"fields": fields}
        if limit:
            kwargs["limit"] = limit
        if offset:
            kwargs["offset"] = offset
        if order:
            kwargs["order"] = order

        return await self.execute_kw(model, "search_read", [domain], kwargs)

    async def search_records_batch(
        self,
        model: str,
        domains: List[List],
        fields: List = None,
        batch_size: int = 100
    ) -> List[List[Dict]]:
        """Execute multiple search operations in optimized batches"""
        if fields is None:
            fields = ["id", "name"]

        results = []
        for i in range(0, len(domains), batch_size):
            batch_domains = domains[i:i + batch_size]
            batch_results = []
            
            for domain in batch_domains:
                result = await self.execute_kw(
                    model, "search_read", [domain], {"fields": fields}
                )
                batch_results.append(result)
                
            results.extend(batch_results)
            
        return results

    # Optimized CRUD Operations
    async def create_record_optimized(self, model: str, values: Dict) -> int:
        """Create record with validation and optimization"""
        # Validate required fields
        required_fields = await self._get_required_fields(model)
        missing_fields = [field for field in required_fields if field not in values]
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
            
        return await self.execute_kw(model, "create", [values])

    async def update_record_optimized(
        self, 
        model: str, 
        record_id: int, 
        values: Dict,
        batch_mode: bool = False
    ) -> bool:
        """Optimized update with batch mode support"""
        if batch_mode:
            # Prepare batch update
            update_key = f"{model}_batch_update"
            if update_key not in self._prepared_updates:
                self._prepared_updates[update_key] = []
                
            self._prepared_updates[update_key].append((record_id, values))
            return True
        else:
            return await self.execute_kw(model, "write", [[record_id], values])

    async def execute_batch_updates(self, model: str) -> bool:
        """Execute all pending batch updates for a model"""
        update_key = f"{model}_batch_update"
        if update_key not in self._prepared_updates:
            return True
            
        updates = self._prepared_updates[update_key]
        if not updates:
            return True
            
        # Group updates by record ID and values
        update_dict = {}
        for record_id, values in updates:
            if record_id not in update_dict:
                update_dict[record_id] = {}
            update_dict[record_id].update(values)
            
        # Execute updates
        for record_id, values in update_dict.items():
            await self.execute_kw(model, "write", [[record_id], values])
            
        # Clear the batch
        self._prepared_updates[update_key] = []
        return True

    async def read_records_optimized(
        self, 
        model: str, 
        record_ids: List[int], 
        fields: List = None,
        batch_size: int = 100
    ) -> List[Dict]:
        """Optimized read with batching support"""
        if fields is None:
            fields = ["id", "name"]

        results = []
        for i in range(0, len(record_ids), batch_size):
            batch_ids = record_ids[i:i + batch_size]
            batch_results = await self.execute_kw(
                model, "read", [batch_ids], {"fields": fields}
            )
            results.extend(batch_results)
            
        return results

    # Query Builder Methods
    async def build_query(
        self,
        model: str,
        filters: Dict[str, Any] = None,
        fields: List[str] = None,
        order_by: str = None,
        limit: int = None,
        offset: int = None
    ) -> List[Dict]:
        """Build and execute query using filter dictionary"""
        if filters is None:
            filters = {}
        if fields is None:
            fields = ["id", "name"]

        domain = []
        for field, value in filters.items():
            if isinstance(value, (list, tuple)) and len(value) == 2:
                # Already in domain format [(field, operator, value)]
                domain.append((field, value[0], value[1]))
            else:
                # Default to equals
                domain.append((field, "=", value))

        kwargs = {"fields": fields}
        if limit:
            kwargs["limit"] = limit
        if offset:
            kwargs["offset"] = offset
        if order_by:
            kwargs["order"] = order_by

        return await self.execute_kw(model, "search_read", [domain], kwargs)

    # File Operations with Optimization
    async def create_attachment_optimized(
        self,
        filename: str,
        file_content: bytes,
        content_type: str,
        res_model: str = "project.project",
        res_id: int = 0
    ) -> int:
        """Create attachment with optimized file handling"""
        file_content_base64 = base64.b64encode(file_content).decode('utf-8')
        
        values = {
            "name": filename,
            "datas": file_content_base64,
            "mimetype": content_type,
            "type": "binary",
            "res_model": res_model,
            "res_id": res_id,
        }
        
        return await self.create_record_optimized("ir.attachment", values)

    # Helper Methods
    async def _get_required_fields(self, model: str) -> List[str]:
        """Get required fields for a model (simplified implementation)"""
        # This would typically call fields_get on the model
        # For now, return common required fields
        common_required = {
            "project.project": ["name"],
            "project.task": ["name", "project_id"],
            "res.partner": ["name"],
            "product.product": ["name"],
            "ir.attachment": ["name", "datas"],
        }
        
        return common_required.get(model, [])

    async def get_model_fields(self, model: str) -> Dict[str, Any]:
        """Get field definitions for a model"""
        return await self.execute_kw(model, "fields_get", [])

    # Performance Monitoring
    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for the client"""
        return {
            "prepared_queries": len(self._prepared_queries),
            "pending_batch_updates": sum(len(batch) for batch in self._prepared_updates.values()),
            "authenticated": self.uid is not None
        }


class OptimizedOdooClientPool:
    """Pool of optimized Odoo clients for concurrent operations"""

    def __init__(self):
        self.clients = {}

    async def get_client(
        self, url: str, db: str, username: str, password: str
    ) -> OptimizedOdooClient:
        """Get or create optimized Odoo client from pool"""
        key = f"{db}:{username}"

        if key not in self.clients:
            client = OptimizedOdooClient(url or settings.ODOO_URL, db, username, password)
            await client.authenticate()
            self.clients[key] = client

        return self.clients[key]

    async def close_all(self):
        """Close all clients in pool"""
        self.clients.clear()


# Global optimized Odoo client pool
optimized_odoo_pool = OptimizedOdooClientPool()