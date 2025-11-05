import logging
from typing import List, Dict, Any, Optional

from app.auth.authz import authz_call
from app.auth.handle_exceptions import handle_odoo_exceptions
from ..schema.odoo_rpc_payload import PayLoadParams
from ..models.used_model import OdooMod, Funcs
from odoo.cache_me.cache_me import CacheMe
from odoo.tools.str_to_dict import str_to_dict

_logger = logging.getLogger(__name__)


class CustomerController:

    @classmethod
    @handle_odoo_exceptions
    async def get_customers(
        cls, login: str, session: str, token: str, limit: int
    ) -> Optional[List[Dict[str, Any]]]:
        """Get Customer for selected way from session"""
        _logger.info(
            "Get customer list for Saleperson: %s, session name: %s", login, session
        )
        return await authz_call(
            paras=PayLoadParams(
                token=token,
                model=OdooMod.mobile_session,
                func=Funcs.get_customer,
                args=[login, session, limit],
            )
        )

    @classmethod
    async def get_cust_from_cache_first(
        cls, login: str, session: str, token: str, limit: int
    ) -> Optional[List[Dict[str, Any]]]:

        key = f"{session}_{login}_customer"
        cache = CacheMe()
        data = await cache.fetch_from_crm_cache([key])

        if data and str_to_dict(data[0].get(key)):
            _logger.info("Cache hit.")
            return str_to_dict(data[0][key])

        _logger.info("Cache miss.")
        customer = await cls.get_customers(login, session, token, limit)

        if customer:
            await cache.send_me(key=key, value=str(customer))
            _logger.info("Added to Cache.")

        return customer

    @classmethod
    @handle_odoo_exceptions
    async def get_cust_by_cust_id(
        cls, customer_id: str, token: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Check customers from ERP."""
        _logger.info("Checking customer id : %s ", customer_id)
        _domain = [("customer_id", "=", customer_id)]
        return await authz_call(
            paras=PayLoadParams(
                token=token,
                model=OdooMod.partner,
                func=Funcs.search_read,
                fields=["customer_id", "name", "personal_mobile"],
                domain=_domain,
                limit=1,
            )
        )
