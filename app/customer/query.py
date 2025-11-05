class PersonalInfoQuery:

    PINFO_QUERY = """
        SELECT
            ptnr_personal.sync_code AS partner_code,
            CONCAT(nfn.name, '/', ntc.name, '(', nrc.name, ')', TRANSLATE(pipi.nrc_no, '၁၂၃၄၅၆၇၈၉၀', '1234567890')) AS nrc
        FROM frnt_partner_partner_personal ptnr_personal
        INNER JOIN frnt_personal_info_personal_info pipi ON (pipi.id = ptnr_personal.personal_info_id)
        LEFT JOIN nrc_first_number nfn ON nfn.id=pipi.nrc_first_no_id
        LEFT JOIN nrc_township_code ntc ON ntc.id=pipi.nrc_township_code_id
        LEFT JOIN nrc_register_code nrc ON nrc.id=pipi.nrc_register_code
    """
    NATIONALITY_QUERY = """
        SELECT id
        FROM partner_nationality
    """

    NRC_FRIST_NO_QUERY = """
        SELECT id
        FROM nrc_first_number
    """

    NRC_TOWNSHIP_CODE_QUERY = """
        SELECT id
        FROM nrc_township_code
    """

    NRC_REGISTER_CODE_QUERY = """
        SELECT id
        FROM nrc_register_code
    """

class PartnerQuery:
    DETAIL_QUERY = """
    SELECT

coalesce (pp.sync_code,'') AS id,
rp.name,
coalesce(pp.sync_code,'') AS partner_code,
-- crm id
rp.customer_id,
rp.employee_id,
rp.csm_id,
rp.biz_reg_no,
rp.is_reseller,
rp.is_consignee,
CASE WHEN rp.supplier_rank>0 THEN true ELSE false END AS is_vendor,
CASE WHEN rp.customer_rank>0 THEN true ELSE false END AS is_customer,
-- is_sl_partner

--
st.name AS customer_type,


rp.black_list AS is_blacklisted,
pi.personal_phone AS phone,
pi.personal_mobile AS mobile,
pi.other_phone AS other_phone,
rp.email AS email,
parent_pp.sync_code AS related_to,

--  PERSONAL INFO
pn.name AS national,
pi.nrc_type,
pi.other_id AS other_nrc,
pi.passport,
pi.date_of_birth,
pi.live_type,

-- NRC
--
nfn.nrc_first_number_code,

--
nrc_tsp.nrc_township_code,

--
nrc_reg.nrc_register_code,

pi.nrc_no AS nrc_number,
pi.full_nrc,

--  BILLING INFO
pi.collection_method AS bill_collection_method,
--
rc.name AS country_name,
rc.country_code,
--
rcs.name AS state_name,
rcs.state_code,
--
rct.name AS city_name,
rct.city_code,
--
ts.name AS township_name,
ts.township_code,
--
rtw.name AS ward_name,
rtw.ward_code,
--
street.name AS street_name,
street.street_code,
--
house.name AS housing_name,
house.housing_code,
--
bt.name AS billing_township_name,
bt.billing_township_code,
--
addr.building_no,
addr.unit,
addr.room_no,
addr.floor,
addr.block,
addr.cross_street,
addr.billing_zone,
addr.latitude,
addr.longitude,

rp.create_date,
rp.write_date

FROM res_partner rp
LEFT JOIN frnt_partner_partner_personal pp ON pp.partner_id=rp.id
INNER JOIN frnt_personal_info_personal_info pi ON rp.personal_info=pi.id
INNER JOIN frnt_address_frnt_address addr ON addr.id=rp.address_id
LEFT JOIN frnt_service_type st ON st.id=rp.customer_type_id
LEFT JOIN frnt_partner_partner_personal parent_pp ON parent_pp.partner_id=rp.parent_id
LEFT JOIN partner_nationality pn ON pn.id=pi.national_id
LEFT JOIN nrc_first_number nfn ON nfn.id=pi.nrc_first_no_id
LEFT JOIN nrc_township_code nrc_tsp ON nrc_tsp.id=pi.nrc_township_code_id
LEFT JOIN nrc_register_code nrc_reg ON nrc_reg.id=pi.nrc_register_code
LEFT JOIN res_country rc ON rc.id = addr.res_country_id
LEFT JOIN res_country_state rcs ON rcs.id = addr.res_state_id
LEFT JOIN res_city rct ON rct.id = addr.res_city_id
LEFT JOIN res_district_township ts ON ts.id = addr.res_township_id
LEFT JOIN res_town_ward rtw ON rtw.id = addr.res_ward_id
LEFT JOIN res_street_name street ON street.id = addr.street_name_id
LEFT JOIN res_housing_name house ON house.id = addr.housing_id
LEFT JOIN billing_township bt ON bt.id=addr.billing_township_id

"""
    PARTNER_DETAIL_WHERE_CLAUSE = " WHERE pp.sync_code = $1 "

    CUSTOMER_DETAIL_WHERE_CLAUSE = " WHERE rp.customer_id = $1 "

    INFO_QUERY = """
    SELECT
    pp.sync_code AS id,
    pp.sync_code AS partner_code,
    rp.name,
    rp.customer_id,
    rp.active,
    pi.full_nrc,
    pi.personal_phone AS phone,
    pi.personal_mobile AS mobile,
    pi.other_phone,
    cus_type.name AS customer_type,
    rp.external_company_id,
    rp.is_company
    """

    COMMON_QUERY = """
    FROM res_partner rp
    INNER JOIN frnt_partner_partner_personal pp ON rp.id=pp.partner_id
    INNER JOIN frnt_personal_info_personal_info pi ON rp.personal_info=pi.id
    LEFT JOIN frnt_service_type cus_type ON cus_type.id=rp.customer_type_id
    {filter}
    {sort}
    {range}
    """

class PartnerDeviceQuery:
    INFO_QUERY = """
    SELECT

    pd.id,
    pd.date_activated,
    pd.device_id,
    pd.state,
    rp.name AS customer_name,
    rp.customer_id,
    pd.service_id,
    pp.sync_code AS partner_id
    """

    COMMON_QUERY = """
    FROM frnt_subs_stock_partner_device pd
    INNER JOIN res_partner rp ON rp.id=pd.partner_id
    INNER JOIN frnt_partner_partner_personal pp ON pp.partner_id = rp.id
    INNER JOIN frnt_personal_info_personal_info pi ON pi.id=rp.personal_info
    {filter}
    {sort}
    {range}
    """
