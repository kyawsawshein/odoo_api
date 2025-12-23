"""Frontend API router for project and task management with Odoo synchronization"""

from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends

from app.api.models.models import SyncResponse
from app.auth.api.v1 import validate_token
from app.auth.session_auth import get_session_odoo_connection
from app.dependency import db
from app.mrp.api.route_name import Route
from app.mrp.controllers.mrp_controller import MRPController
from app.mrp.schemas.mrp import OrderSchema, WorkOrderSchema

logger = structlog.get_logger()


router = APIRouter(
    prefix="/mrp",
    tags=["MRP"],
    dependencies=[Depends(validate_token)],
)


@router.get(Route.orders, response_model=List[OrderSchema])
async def get_orders(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    odoo_connection=Depends(get_session_odoo_connection),
    db_connection=Depends(db.connection),
):
    """Get MRP orderd"""
    return await MRPController(odoo_connection, db_connection).get_orders(
        skip=skip, limit=limit, search=search
    )


@router.get(Route.order_id, response_model=OrderSchema)
async def get_order(
    order_id: int,
    odoo_connection=Depends(get_session_odoo_connection),
    db_connection=Depends(db.connection),
):
    """Get MRP order by id"""
    return await MRPController(odoo_connection, db_connection).get_order(order_id)


@router.get(Route.order_workorder, response_model=List[WorkOrderSchema])
async def get_order_workorder(
    order_id: int,
    odoo_connection=Depends(get_session_odoo_connection),
    db_connection=Depends(db.connection),
):
    """Get specific task details from frontend"""
    return await MRPController(odoo_connection, db_connection).get_order_workorder(
        order_id
    )


@router.get(Route.workorders, response_model=List[WorkOrderSchema])
async def get_workorders(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    odoo_connection=Depends(get_session_odoo_connection),
    db_connection=Depends(db.connection),
):
    """Get specific task details from frontend"""
    return await MRPController(odoo_connection, db_connection).get_workorders(
        skip=skip, limit=limit, search=search
    )


@router.get(Route.workorder_id, response_model=WorkOrderSchema)
async def get_workorder(
    workcenter_id: int,
    odoo_connection=Depends(get_session_odoo_connection),
    db_connection=Depends(db.connection),
):
    """Get specific task details from frontend"""
    return await MRPController(odoo_connection, db_connection).get_workorder(
        workcenter_id
    )


@router.get(Route.start_workorder, response_model=SyncResponse)
async def start_workorder(
    workcenter_id: int,
    odoo_connection=Depends(get_session_odoo_connection),
    db_connection=Depends(db.connection),
):
    """Set to start workorder."""
    return await MRPController(odoo_connection, db_connection).start_workorder(
        workcenter_id
    )


@router.get(Route.pending_workorder, response_model=SyncResponse)
async def pending_workorder(
    workcenter_id: int,
    odoo_connection=Depends(get_session_odoo_connection),
    db_connection=Depends(db.connection),
):
    """Set to pending workorder."""
    return await MRPController(odoo_connection, db_connection).pending_workorder(
        workcenter_id
    )


@router.get(Route.end_workorder, response_model=SyncResponse)
async def end_workorder(
    workcenter_id: int,
    odoo_connection=Depends(get_session_odoo_connection),
    db_connection=Depends(db.connection),
):
    """Set to end workorder."""
    return await MRPController(odoo_connection, db_connection).end_workorder(
        workcenter_id
    )
