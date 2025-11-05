from typing import List, Tuple
from fastapi import HTTPException, status
from asyncpg import Connection
from odoo_shared.frnt_partner.datamodels.partner_schema import PartnerDetailsApi

from odoo.dependency import Odoo
from odoo.core.param_parser import get_records, RestParamsRaw, RestParams, record_not_found_exception
from odoo.external.kore.kore import KoreApi
from odoo.subscription.crud.subscription_crud import SubCRUD
from .schemas import CustomerFilter, CustomerResponse, PartnerInfoRequestParam, PartnerResponseData,\
    CustomerInfoApi, CUSTOMER_INFO_FILTER_MAP
from .customer_utils import NumberValidationError
from .crud import CustomerCRUD

class CustomerController:
    def __init__(self) -> None:
        pass

    @classmethod
    async def get_customer_by_filter(cls, filter_data: CustomerFilter, db_conn: Connection):
        try:
            customer_list = await CustomerCRUD.get_customer_by_filter(filter_data=filter_data, db_conn=db_conn)
        except NumberValidationError as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="NRC number should only be number in (MM or ENG)") from err
        if not customer_list:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Customer not found with the filter : {filter_data}")
        return CustomerResponse(data=customer_list)

    @classmethod
    async def get_partner_code(cls, partner_info:PartnerInfoRequestParam, db_conn: Connection,\
        odoo_conn: Odoo) -> PartnerResponseData:
        personal = await CustomerCRUD.check_partner(partner_info=partner_info, db_conn=db_conn)
        if not personal:
            personal = await CustomerCRUD.create_personal_info(partner_info=partner_info, db_conn=db_conn, odoo=odoo_conn)
        return personal

    @classmethod
    async def patch_param(cls, param: RestParams, db_conn: Connection):
        cid = param.filter.get('cid')
        if cid:
            if len(cid) > 5:
                status_code, data = await KoreApi.search_group_by_cid(cid=param.filter.get('cid'))
                if status_code == 200 and data.data.member:
                    customer_id = await SubCRUD.get_customer_id_by_group_id(data.data.member.group.group_ref_id, db_conn)
                    if customer_id:
                        param.filter.update({'customer_id': customer_id})
                        return
            raise record_not_found_exception()

    @classmethod
    async def get_customers(cls, param: RestParamsRaw, db_conn: Connection)->Tuple[List[CustomerInfoApi], int]:
        return await get_records(
            get_records_fun = CustomerCRUD.get_customers,
            get_count_fun   = CustomerCRUD.get_customer_count,
            filter_map      = CUSTOMER_INFO_FILTER_MAP,
            param           = param,
            db_conn         = db_conn,
            patch_param     = cls.patch_param
        )

    @staticmethod
    def get_full_address(data: dict) -> str:
        return ", ".join(filter(None,[
            f"Room {data['room_no']}" if data.get('room_no') not in (None, '') else None,
            f"Floor {data['floor']}" if data.get('floor') not in (None, '') else None,
            f"Unit {data['unit']}" if data.get('unit') not in (None, '') else None,
            f"Building No{data['building_no']}" if data.get('building_no') not in (None, '') else None,
            *[
                str(data[key]) for key in [
                    'housing_name', 'street_name', 'block', 'ward_name',
                    'township_name', 'city_name', 'state_name',
                    'country_name', 'billing_township_name'
                ] if data.get(key) not in (None, '')
            ]
        ]))

    @classmethod
    async def get_customer_details(cls, partner_code: str, db_conn: Connection)->PartnerDetailsApi:
        data = await CustomerCRUD.get_customer_datails(partner_code=partner_code, db_conn=db_conn)
        if data:
            data = dict(data)
            data['full_address'] = CustomerController.get_full_address(data=data)
            data['nrc'] = data
            data['personal_info'] = data
            data['billing_address'] = data
            data['billing_info'] = data
            return PartnerDetailsApi.parse_obj(data)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Customer[{partner_code}] not found")
