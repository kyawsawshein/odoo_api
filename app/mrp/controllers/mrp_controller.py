"""Frontend API router for mrp and task management with Odoo synchronization"""

import base64
from typing import Any, Dict, List, Optional

import asyncpg
import structlog
from fastapi import HTTPException, status

from app.auth.models.models import User
from app.mrp.crud.crud import MRPCrud

# Database dependency is now passed as parameter, not imported at module level
from app.mrp.models.model import Order, WorkOrder
from app.mrp.schemas.mrp import (
    LabourCost,
    MaterialCost,
    OrderSchema,
    OverheadCost,
    WorkOrderSchema,
)
from app.utils.model_name import Method, ModelName

logger = structlog.get_logger()


class MRPController:
    def __init__(
        self,
        odoo_connection,
        db_connection: asyncpg.connection,
    ):
        self.odoo = odoo_connection
        self.db = db_connection
        self.logger = logger

    async def get_records(
        self, model: str, method: str, domain: list, kwargs: dict = None
    ) -> List[int]:
        return await self.odoo.execute_kw(
            model=model, method=method, args=[domain], kwargs=kwargs
        )

    async def get_order_ids(
        self, model: str, method: str, domain: list, kwargs: dict = None
    ) -> List[int]:
        """Get projects with optional search"""
        try:
            # Search projects in Odoo
            return await self.get_records(
                model=model, method=method, domain=domain, kwargs=kwargs
            )
        except Exception as e:
            self.logger.error("Failed to fetch projects", error=str(e))
            raise

    async def get_order(self, order_id: int) -> OrderSchema:
        """Get specific mrp by ID with full details"""
        try:
            # Read mrp details
            order_fields = list(Order.model_fields.keys())
            domain = [("id", "=", order_id)]
            kwargs = {"fields": order_fields}
            order_data = await self.get_records(
                model=ModelName.PRODUCTION,
                method=Method.SEARCH_READ,
                domain=domain,
                kwargs=kwargs,
            )
            if not order_data:
                return None

            mrp = Order(**order_data[0])
            return OrderSchema(
                id=mrp.id,
                name=mrp.name,
                product=mrp.product_id.model_dump(),
                status=mrp.state,
            )
        except Exception as e:
            self.logger.error("Failed to fetch mrp", order_id=order_id, error=str(e))
            raise

    async def get_orders(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
    ) -> List[OrderSchema]:
        """Get mrp dashboard data"""
        try:
            # Get mrp list for dashboard
            domain = [("state", "in", ("draft", "confirmed", "progress"))]
            if search:
                domain.extend([("name", "ilike", f"%{search}%")])
            kwargs = {"offset": skip, "limit": limit}
            order_list = await self.get_order_ids(
                model=ModelName.PRODUCTION,
                method=Method.SEARCH,
                domain=domain,
                kwargs=kwargs,
            )
            # Get full details for each mrp
            orders = []
            for order_id in order_list:
                order = await self.get_order(order_id)
                if order:
                    orders.append(order)
            return orders
        except Exception as e:
            self.logger.error("Error : %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch mrp dashboard: {str(e)}",
            )

    async def get_order_workorder(self, order_id: int) -> List[WorkOrderSchema]:
        try:
            workorder_fields = list(WorkOrder.model_fields.keys())
            domain = [("production_id", "=", order_id)]
            kwargs = {"fields": workorder_fields}
            workorder_data = await self.odoo.execute_kw(
                model=ModelName.WORKORDER,
                method=Method.SEARCH_READ,
                args=[domain],
                kwargs=kwargs,
            )
            if not workorder_data:
                return None

            workorders = []
            for workorder in workorder_data:
                work = WorkOrder(**workorder)
                workorders.append(
                    WorkOrderSchema(
                        id=work.id,
                        work_center_id=work.workcenter_id.model_dump(),
                        product_id=work.product_id.model_dump(),
                        duration_expected=work.duration_expected,
                        status=work.state,
                    )
                )
            return workorders
        except Exception as err:
            self.logger.error("Failed to fetch workorders", error=str(err))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch mrp workorders: {str(err)}",
            )

    async def get_workorders(
        self, skip: int, limit: int, search: Optional[str] = None
    ) -> List[WorkOrderSchema]:
        try:
            domain = [("state", "in", ("blocked", "ready", "progress"))]
            if search:
                domain.extend([("name", "ilike", f"%{search}%")])
            workorder_fields = list(WorkOrder.model_fields.keys())
            kwargs = {"fields": workorder_fields, "offset": skip, "limit": limit}
            workorder_data = await self.get_records(
                model=ModelName.WORKORDER,
                method=Method.SEARCH_READ,
                domain=domain,
                kwargs=kwargs,
            )

            if not workorder_data:
                return None

            workorders = []
            for workorder in workorder_data:
                work = WorkOrder(**workorder)
                workorders.append(
                    WorkOrderSchema(
                        id=work.id,
                        work_center_id=work.workcenter_id.model_dump(),
                        product_id=work.product_id.model_dump(),
                        duration_expected=work.duration_expected,
                        status=work.state,
                    )
                )
            return workorders
        except Exception as err:
            self.logger.error("Failed to fetch workorders", error=str(err))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch workorders: {str(err)}",
            )

    async def get_workorder(self, workorder_id: int):
        try:
            workorder_fields = list(WorkOrder.model_fields.keys())
            domain = [("id", "=", workorder_id)]
            kwargs = {"fields": workorder_fields}
            workorder_data = await self.odoo.execute_kw(
                model=ModelName.WORKORDER,
                method=Method.SEARCH_READ,
                args=[domain],
                kwargs=kwargs,
            )
            if not workorder_data:
                return None
            workorder = WorkOrder(**workorder_data[0])
            return workorder

        except Exception as err:
            raise
