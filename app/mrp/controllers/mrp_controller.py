"""Frontend API router for mrp and task management with Odoo synchronization"""

import base64
from typing import Any, Dict, List, Optional

import asyncpg
import structlog
from fastapi import HTTPException, status

# Database dependency is now passed as parameter, not imported at module level
from app.api.models.models import SyncResponse
from app.auth.models.models import User
from app.mrp.crud.crud import MRPCrud
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
    ):
        self.odoo = odoo_connection
        self.logger = logger

    async def get_order(self, order_id: int) -> OrderSchema:
        """Get specific mrp by ID with full details"""
        try:
            # Read mrp details
            domain = [("id", "=", order_id)]
            kwargs = {"fields": list(Order.model_fields.keys())}
            order_data = await self.odoo.execute_kw(
                model=ModelName.PRODUCTION,
                method=Method.SEARCH_READ,
                args=[domain],
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
            kwargs = {
                "fields": list(Order.model_fields.keys()),
                "offset": skip,
                "limit": limit,
            }
            if search:
                domain.extend([("name", "ilike", f"%{search}%")])
            order_list = await self.odoo.execute_kw(
                model=ModelName.PRODUCTION,
                method=Method.SEARCH_READ,
                args=[domain],
                kwargs=kwargs,
            )
            # Get full details for each mrp
            orders = []
            for order in order_list:
                mrp = Order(**order)
                orders.append(
                    OrderSchema(
                        id=mrp.id,
                        name=mrp.name,
                        product=mrp.product_id.model_dump(),
                        status=mrp.state,
                    )
                )
            return orders
        except Exception as e:
            self.logger.error("Error : %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch mrp dashboard: {str(e)}",
            )

    async def get_order_workorder(self, order_id: int) -> List[WorkOrderSchema]:
        try:
            domain = [("production_id", "=", order_id)]
            kwargs = {"fields": list(WorkOrder.model_fields.keys())}
            workorder_data = await self.odoo.execute_kw(
                model=ModelName.WORKORDER,
                method=Method.SEARCH_READ,
                args=[domain],
                kwargs=kwargs,
            )

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
            kwargs = {
                "fields": list(WorkOrder.model_fields.keys()),
                "offset": skip,
                "limit": limit,
            }
            workorder_data = await self.odoo.execute_kw(
                model=ModelName.WORKORDER,
                method=Method.SEARCH_READ,
                args=[domain],
                kwargs=kwargs,
            )

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

    async def get_workorder(self, workorder_id: int) -> WorkOrderSchema:
        try:
            domain = [("id", "=", workorder_id)]
            kwargs = {"fields": list(WorkOrder.model_fields.keys())}
            workorder = await self.odoo.execute_kw(
                model=ModelName.WORKORDER,
                method=Method.SEARCH_READ,
                args=[domain],
                kwargs=kwargs,
            )
            if not workorder:
                return None

            workorder = WorkOrder(**workorder[0])
            return WorkOrderSchema(
                id=workorder.id,
                work_center_id=workorder.workcenter_id.model_dump(),
                product_id=workorder.product_id.model_dump(),
                duration_expected=workorder.duration_expected,
                status=workorder.state,
            )
        except Exception as err:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch workorder id : {str(err)}",
            ) from err

    async def start_workorder(self, workorder_id: int) -> SyncResponse:
        try:
            await self.odoo.execute_kw(
                model=ModelName.WORKORDER,
                method="rpc_button_start",
                args=[workorder_id],
            )
            return SyncResponse(success=True, message="Workorder started")
        except Exception as err:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to start workorder : {str(err)}",
            ) from err

    async def pending_workorder(self, workorder_id: int) -> SyncResponse:
        try:
            await self.odoo.execute_kw(
                model=ModelName.WORKORDER,
                method="end_previous",
                args=[workorder_id],
            )
            return SyncResponse(success=True, message="Workorder pending")
        except Exception as err:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to pending workorder : {str(err)}",
            ) from err

    async def end_workorder(self, workorder_id: int) -> SyncResponse:
        try:
            await self.odoo.execute_kw(
                model=ModelName.WORKORDER,
                method="button_finish",
                args=[workorder_id],
            )
            return SyncResponse(success=True, message="Workorder ended")
        except Exception as err:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to end workorder: {str(err)}",
            ) from err
