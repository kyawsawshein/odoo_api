from dataclasses import dataclass

@dataclass
class CustomerModel:
    _table = "res_partner"
    _partner_info_table = "frnt_partner.partner_personal"
