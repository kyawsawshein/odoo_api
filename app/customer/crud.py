from typing import List
import re
from asyncpg import Connection
from fastapi import HTTPException

from odoo.dependency import Odoo
from odoo.core.query_executor import prepare_and_fetch, prepare_and_fetchrow
from odoo.core.param_parser import RestParams, prepare_query, COUNT_QUERY
from ..invoicing.schema.invoice_schema import Invoice, InvoiceStatus
from .customer_utils import NRC_REGEX, is_eng, number_to_mm, number_to_eng
from .schemas import Customer, CustomerFilter, PartnerInfoRequestParam, PartnerResponseData, PersonalInfo,\
    NrcType, CustomerInfoApi
from .query import PersonalInfoQuery, PartnerQuery
from .models import CustomerModel

BASE_QUERY_STRING = """
        SELECT

        rp.id AS id,
        rp.name AS name,
        rp.customer_id AS customer_id,
        ptnr_personal.sync_code AS partner_code,
        pipi.personal_mobile AS mobile,
        pipi.personal_phone AS phone,
        pipi.other_phone AS other_phone,
        rp.email AS email,
        rp.employee_id AS employee_id,
        CONCAT(nfn.eng_code, '/', ntc.eng_code, '(', nrc.eng_code, ')', TRANSLATE(pipi.nrc_no, '၁၂၃၄၅၆၇၈၉၀', '1234567890')) AS nrc,
        pipi.other_id AS other_id,
        pipi.passport AS passport

        FROM frnt_partner_partner_personal ptnr_personal
        INNER JOIN res_partner rp ON rp.id = ptnr_personal.partner_id
        INNER JOIN frnt_personal_info_personal_info pipi ON ptnr_personal.personal_info_id = pipi.id
        LEFT JOIN nrc_first_number nfn ON nfn.id=pipi.nrc_first_no_id
        LEFT JOIN nrc_township_code ntc ON ntc.id=pipi.nrc_township_code_id
        LEFT JOIN nrc_register_code nrc ON nrc.id=pipi.nrc_register_code
        """

class CustomerCRUD:
    def __init__(self, db: Connection=None, odoo: Odoo=None, table_name: str = "res.partner") -> None:
        self.db = db
        self.odoo = odoo
        self.table_name = table_name

    @classmethod
    async def get_customer_count(cls, rest_param: RestParams, filter_map: dict, db_conn: Connection)->int:
        rest_param = rest_param.copy()
        rest_param.range = None
        rest_param.sort = None
        query, query_args = prepare_query(query=f"{COUNT_QUERY} {PartnerQuery.COMMON_QUERY}",\
            filter_map=filter_map, rest_param=rest_param)
        res = await prepare_and_fetchrow(db_conn, query, *query_args)
        return res.get('count')

    @classmethod
    async def get_customers(cls, rest_param: RestParams, filter_map: dict, db_conn: Connection)->list:
        query, query_args = prepare_query(query=f"{PartnerQuery.INFO_QUERY} {PartnerQuery.COMMON_QUERY}",\
            filter_map=filter_map, rest_param=rest_param)
        records = await prepare_and_fetch(db_conn, query, *query_args)
        if records:
            return [ CustomerInfoApi.parse_obj(tmp) for tmp in records ]
        return []

    @classmethod
    async def get_customer_datails(cls, partner_code: str, db_conn: Connection)->dict:
        return await prepare_and_fetchrow(db_conn, f"{PartnerQuery.DETAIL_QUERY} {PartnerQuery.PARTNER_DETAIL_WHERE_CLAUSE}",\
            partner_code)

    @classmethod
    async def get_customer_datails_by_customer_id(cls, customer_id: str, db_conn: Connection)->dict:
        return await prepare_and_fetchrow(db_conn, f"{PartnerQuery.DETAIL_QUERY} {PartnerQuery.CUSTOMER_DETAIL_WHERE_CLAUSE}",\
            customer_id)

    async def get_by_customer_id(self, customer_id: str) -> Customer:
        customer = None
        records = await self.db.fetch(
            BASE_QUERY_STRING + """
            WHERE rp.customer_id=$1 LIMIT 1;
            """, customer_id
        )
        for record in records:
            customer = Customer.parse_obj(record)
        if not customer:
            raise HTTPException(status_code=404, detail=f"Customer ID [{customer_id}] not found!")
        return customer

    async def get_customer_invoices(self, customer_id: str, status: InvoiceStatus) -> List[Invoice]:
        invoices = []
        # TODO Call to invoicing CURD with customer filter
        return invoices

    async def get_partner_id_by_customer_id(self, customer_id: str) -> int:
        record = await self.db.fetchrow(
            f"""
            SELECT id FROM {self.table_name.replace('.', '_')} WHERE customer_id=$1 LIMIT 1;
            """, customer_id
        )
        return record.get('id') if record else False

    @classmethod
    def prepare_nrc_filter(cls, filter_data: CustomerFilter, query_params: List) -> str:
        nrc_filter_query = ""
        reg = re.match(NRC_REGEX, filter_data.nrc)
        if reg:
            nrc_first_no, nrc_township_code, _, nrc_register_code, _, nrc_no = reg.groups()
            if is_eng(nrc_first_no):
                nrc_filter_query += f" nfn.eng_code=${len(query_params) + 1} "
            else:
                nrc_filter_query += f" nfn.name=${len(query_params) + 1} "
            query_params.append(nrc_first_no)

            if is_eng(nrc_township_code):
                nrc_filter_query += f" AND LOWER(ntc.eng_code)=${len(query_params) + 1} "
                query_params.append(nrc_township_code.lower())
            else:
                nrc_filter_query += f" AND ntc.name=${len(query_params) + 1} "
                query_params.append(nrc_township_code)

            if is_eng(nrc_register_code):
                nrc_filter_query += f" AND LOWER(nrc.eng_code) = ${len(query_params) + 1} "
                query_params.append(nrc_register_code.lower())
            else:
                nrc_filter_query += f" AND nrc.name = ${len(query_params) + 1} "
                query_params.append(nrc_register_code)

            nrc_filter_query += f" AND (pipi.nrc_no = ${len(query_params) + 1} OR pipi.nrc_no = ${len(query_params) + 2}) "
            query_params.extend([number_to_mm(nrc_no), number_to_eng(nrc_no)])
        else:
            nrc_filter_query += f" pipi.other_id = ${len(query_params) + 1} OR pipi.passport = ${len(query_params) + 2} "
            query_params.extend([filter_data.nrc, filter_data.nrc])
        return nrc_filter_query

    @classmethod
    def prepare_customer_id_filter(cls, filter_data: CustomerFilter, query_params: List):
        customer_id_filter_query = ""
        customer_id_filter_query += f" rp.customer_id=${len(query_params) + 1} "
        query_params.append(filter_data.customer_id)
        return customer_id_filter_query

    @classmethod
    def prepare_employee_id_filter(cls, filter_data: CustomerFilter, query_params: List):
        employee_id_filter_query = ""
        employee_id_filter_query += f" rp.employee_id=${len(query_params) + 1} "
        query_params.append(filter_data.employee_id)
        return employee_id_filter_query

    @classmethod
    async def get_customer_by_filter(cls, filter_data: CustomerFilter, db_conn: Connection) -> List[Customer]:
        query_string = BASE_QUERY_STRING
        query_params = []

        filter_count = 0

        nrc_filter_query = ""
        customer_id_filter_query = ""
        employee_id_filter_query = ""
        where_clause = ""

        if filter_data.customer_id:
            filter_count += 1
            customer_id_filter_query += cls.prepare_customer_id_filter(filter_data=filter_data, query_params=query_params)

        if filter_data.nrc:
            filter_count += 1
            nrc_filter_query += cls.prepare_nrc_filter(filter_data=filter_data, query_params=query_params)

        if filter_data.employee_id:
            filter_count += 1
            employee_id_filter_query += cls.prepare_employee_id_filter(filter_data=filter_data, query_params=query_params)

        if filter_count > 1:
            if filter_data.customer_id:
                where_clause += f" WHERE ({customer_id_filter_query}) "
            if filter_data.nrc:
                where_clause += f" WHERE ({nrc_filter_query}) " if not where_clause else f" OR ({nrc_filter_query}) "
            if filter_data.employee_id:
                where_clause += f" WHERE ({employee_id_filter_query}) " if not where_clause else f" OR ({employee_id_filter_query}) "

        else:
            where_clause += f" WHERE {customer_id_filter_query}{nrc_filter_query}{employee_id_filter_query} "

        data = await prepare_and_fetch(db_conn, query_string + where_clause, *query_params)
        return [ Customer.parse_obj(customer) for customer in data ] if data else []

    @classmethod
    def prepare_partner_info_filter(cls, partner_info:PartnerInfoRequestParam) -> str:
        query_filter = ""
        if not partner_info.nationality_code:
            raise HTTPException(status_code=400, detail="The requested data did not complete. Naitonality code must not be null.")
        if partner_info.nrc:
            nrc_info = partner_info.nrc
            if not (nrc_info.nrc_first_number_code and nrc_info.nrc_township_code and nrc_info.nrc_register_code\
                and nrc_info.nrc_number):
                raise HTTPException(status_code=400, detail="The requested data did not complete for NRC Info.")

            query_filter = f"""nfn.nrc_first_number_code = '{nrc_info.nrc_first_number_code}'
                AND ntc.nrc_township_code = '{nrc_info.nrc_township_code}'
                AND nrc.nrc_register_code = '{nrc_info.nrc_register_code}'
                AND pipi.nrc_no = '{nrc_info.nrc_number}'"""

        elif partner_info.passport:
            query_filter = f"pipi.passport = '{partner_info.passport}'"
        elif partner_info.other_id:
            query_filter = f"pipi.other_id = '{partner_info.other_id}'"
        else:
            raise HTTPException(status_code=400, detail="The requested data did not complete.")

        return query_filter

    @classmethod
    async def check_partner(cls, partner_info:PartnerInfoRequestParam, db_conn:Connection) -> PartnerResponseData:
        partner_response = None
        filter_query = cls.prepare_partner_info_filter(partner_info=partner_info)
        query_str = PersonalInfoQuery.PINFO_QUERY + f" WHERE {filter_query} ORDER BY pipi.id DESC LIMIT 1;"
        records = await prepare_and_fetch(db_conn, query_str)
        for record in records:
            partner_response = PartnerResponseData.parse_obj(record)
        return partner_response

    @classmethod
    async def get_personal_info_data(cls, query_str:str, filter_str:str, db_conn:Connection) -> str:
        records =  await prepare_and_fetch(db_conn, query_str)
        if not records:
            raise HTTPException(status_code=400, detail=f"{filter_str} have not found.")
        for record in records:
            result = record[0]
        return result

    @classmethod
    async def prepare_personal_info(cls, partner_info:PartnerInfoRequestParam, db_conn:Connection) -> PersonalInfo:
        nationality_query_str = f"""{PersonalInfoQuery.NATIONALITY_QUERY}
            WHERE nationality_code = '{partner_info.nationality_code}' LIMIT 1"""
        national_id = await cls.get_personal_info_data(query_str=nationality_query_str, filter_str="Nationality Code",\
            db_conn=db_conn)
        personal_info_data = PersonalInfo(national_id=national_id)

        if partner_info.nrc:
            personal_info_data.is_nrc = True
            personal_info_data.nrc_type = NrcType.STANDARD
            nfc_query_str = f"""{PersonalInfoQuery.NRC_FRIST_NO_QUERY}
                WHERE nrc_first_number_code = '{partner_info.nrc.nrc_first_number_code}'"""
            nrc_first_no_id = await cls.get_personal_info_data(query_str=nfc_query_str, filter_str="NRC Frist No Code",\
                db_conn=db_conn)
            personal_info_data.nrc_first_no_id = nrc_first_no_id

            ntc_query_str = f"""{PersonalInfoQuery.NRC_TOWNSHIP_CODE_QUERY}
                WHERE nrc_township_code = '{partner_info.nrc.nrc_township_code}'"""
            nrc_township_code_id = await cls.get_personal_info_data(query_str=ntc_query_str, filter_str='NRC Township Code',\
                db_conn=db_conn)
            personal_info_data.nrc_township_code_id = nrc_township_code_id

            nrc_query_str = f"""{PersonalInfoQuery.NRC_REGISTER_CODE_QUERY}
                WHERE nrc_register_code = '{partner_info.nrc.nrc_register_code}'"""
            nrc_register_code = await cls.get_personal_info_data(query_str=nrc_query_str, filter_str='NRC Register Code',\
                db_conn=db_conn)
            personal_info_data.nrc_register_code = nrc_register_code
            personal_info_data.nrc_no = partner_info.nrc.nrc_number
        elif partner_info.other_id:
            personal_info_data.is_nrc = True
            personal_info_data.nrc_type = NrcType.OTHER
            personal_info_data.other_id = partner_info.other_id
        else:
            personal_info_data.is_nrc = False
            personal_info_data.passport = partner_info.passport

        return personal_info_data

    @classmethod
    async def create_personal_info(cls, partner_info:PartnerInfoRequestParam, db_conn:Connection, odoo:Odoo)\
        -> PartnerResponseData:
        personal_info = await cls.prepare_personal_info(partner_info=partner_info, db_conn=db_conn)
        method = "create_partner_personal"
        result = odoo.models.execute_kw(*odoo.secrets, CustomerModel._partner_info_table, method,\
            [personal_info.dict(exclude_none=True, exclude_unset=True)])
        return PartnerResponseData(**result)
