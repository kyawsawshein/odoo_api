import logging
from typing import List, Dict, Any, Optional

from odoo.authz.authz import authz_call


from app.auth.handle_exceptions import handle_odoo_exceptions
from app.core.schemas import PayLoadParams
from ..models.used_model import OdooMod, Funcs
from odoo.cache_me.cache_me import CacheMe
from odoo.tools.str_to_dict import str_to_dict

_logger = logging.getLogger(__name__)


class ProductController:

    @classmethod
    @handle_odoo_exceptions
    async def get_product(
        cls, login: str, session_name: str, token: str
    ) -> Optional[List[Dict[str, Any]]]:
        _logger.info(
            "Getting product list for saleperson: %s, session: %s", login, session_name
        )
        return await authz_call(
            paras=PayLoadParams(
                token=token,
                model=OdooMod.mobile_session,
                func=Funcs.get_product,
                args=[login, session_name],
            )
        )

    @classmethod
    async def get_prod_from_cache_first(
        cls, login: str, session_name: str, token: str
    ) -> Optional[List[Dict[str, Any]]]:

        key = f"{session_name}_{login}_product"
        cache = CacheMe()
        data = await cache.fetch_from_crm_cache([key])

        if data and str_to_dict(data[0].get(key)):
            _logger.info("Cache hit.")
            return str_to_dict(data[0][key])

        _logger.info("Cache miss.")
        product = await cls.get_product(login, session_name, token)

        if product:
            await cache.send_me(key=key, value=str(product))
            _logger.info("Added to Cache.")

        return product
