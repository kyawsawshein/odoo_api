from typing import Optional
from datetime import date
from pydantic import BaseModel
from odoo_shared.frnt_order.datamodels.order_schema import OrderDetail
from odoo.core.param_parser import FieldFilter, FieldType, QueryHow

class OrderInfoApi(BaseModel):
    id                : str
    order_type_name   : Optional[str]
    order_date        : Optional[date]
    poi               : str
    status            : Optional[str]
    new_customer_name : Optional[str]
    partner_code      : Optional[str]
    customer_id       : Optional[str]
    customer_name     : Optional[str]
    service_type_name : Optional[str]
    package_name      : Optional[str]
    installation_id   : Optional[str]
    installation_type_name : Optional[str]

ORDER_RA_FILTER_MAP = {
    'id'                     : FieldFilter(field='po.idorder_id',        how=QueryHow.EQ,    field_type=FieldType.VARCHAR),
    'order_type_name'        : FieldFilter(field='ot.name',              how=QueryHow.ILIKE, field_type=FieldType.VARCHAR),
    'order_date'             : FieldFilter(field='po.order_date',        how=QueryHow.EQ,    field_type=FieldType.DATE),
    'poi'                    : FieldFilter(field='po.order_id',          how=QueryHow.EQ,    field_type=FieldType.VARCHAR),
    'status'                 : FieldFilter(field='po.state',             how=QueryHow.EQ,    field_type=FieldType.VARCHAR),
    'new_customer_name'      : FieldFilter(field='po.new_customer_name', how=QueryHow.ILIKE, field_type=FieldType.VARCHAR),
    'partner_code'           : FieldFilter(field='pp.sync_code',         how=QueryHow.EQ,    field_type=FieldType.VARCHAR),
    'customer_id'            : FieldFilter(field='rp.customer_id',       how=QueryHow.EQ,    field_type=FieldType.VARCHAR),
    'customer_name'          : FieldFilter(field='rp.name',              how=QueryHow.ILIKE, field_type=FieldType.VARCHAR),
    'service_type_name'      : FieldFilter(field='fst.name',             how=QueryHow.ILIKE, field_type=FieldType.VARCHAR),
    'package_name'           : FieldFilter(field='pkg.name',             how=QueryHow.ILIKE, field_type=FieldType.VARCHAR),
    'installation_id'        : FieldFilter(field='inst.installation_no', how=QueryHow.EQ,    field_type=FieldType.VARCHAR),
    'installation_type_name' : FieldFilter(field='inst_type.name',       how=QueryHow.ILIKE, field_type=FieldType.VARCHAR),
}

class TapSin(BaseModel):
    installation_type_id: Optional[int]
    service_type_id     : Optional[int]
    package_id          : Optional[int]
    installation_category : Optional[str] = ""

class OrderDetailApi(OrderDetail):
    tapsin: Optional[TapSin]
