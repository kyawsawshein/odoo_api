import copy
from typing import List, Tuple
from asyncpg import Connection
from fastapi import HTTPException, status

from odoo.core.utils import dt_to_utc
from odoo.core.param_parser import get_records, RestParamsRaw
from ..schema.order import OrderInfoApi, ORDER_RA_FILTER_MAP, OrderDetailApi
from ..crud.order_crud import OrderCRUD

class OrderController:
    def __init__(self) -> None:
        pass

    @classmethod
    async def get_order_detail(cls, poi: str, db_conn: Connection) -> OrderDetailApi:
        output_dict = {}
        order_data = await OrderCRUD.get_order_detail(poi=poi, db_conn=db_conn)
        if not order_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        output_dict.update(dict(order_data))
        dt_to_utc(output_dict)
        billing_address = {}
        new_customer_info = copy.deepcopy(output_dict)
        service_info = copy.deepcopy(output_dict)
        if output_dict.get('billing_address_id'):
            billing_address = dict(await OrderCRUD.get_billing_address(\
                    address_id=output_dict.get('billing_address_id'), db_conn=db_conn))
        if output_dict.get('is_same_with_billing_address'):
            service_info['service_address'] = billing_address
        else:
            service_info['service_address'] = dict(await OrderCRUD.get_po_service_address(poi=poi, db_conn=db_conn))
        output_dict['service_info'] = service_info
        if output_dict.get('partner_code'):
            output_dict['new_customer_info'] = None
        else:
            output_dict['nrc'] = output_dict
            new_customer_info.update({
                'billing_info': {
                    'billing_address': billing_address,
                },
                'personal_info': output_dict
            })
            output_dict['new_customer_info'] = new_customer_info
        tapsin = {}
        if output_dict.get('installation_table_id'):
            output_dict['installation_info'] = dict(await OrderCRUD.get_installation(\
                inst_id=output_dict.get('installation_table_id'), db_conn=db_conn))
            dt_to_utc(output_dict['installation_info'])
            tapsin.update(installation_type_id=output_dict['installation_info'].get('installation_type_id'))
            tapsin.update(installation_category=output_dict['installation_info'].get('installation_category'))
        tapsin.update({
            'service_type_id': output_dict.get('service_type_id'),
            'package_id'     : output_dict.get('package_id')
        })
        output_dict["tapsin"] = tapsin
        return OrderDetailApi.parse_obj(output_dict)

    @classmethod
    async def get_orders(cls, param: RestParamsRaw, db_conn: Connection)->Tuple[List[OrderInfoApi], int]:
        return await get_records(
            get_records_fun = OrderCRUD.get_orders,
            get_count_fun   = OrderCRUD.get_orders_count,
            filter_map      = ORDER_RA_FILTER_MAP,
            param           = param,
            db_conn         = db_conn,
        )
