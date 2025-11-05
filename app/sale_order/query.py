class OrderQuery:

    ORDER_QUERY = """
        SELECT json_build_object(
            'poi', od.order_id,
            'order_type', otype.name,
            'status', od.state,
            'service', json_build_object(
                'service_type', ser.name,
                'OPI', COALESCE(opi.code, ''),
                'package', pack.name,
                'price', od.price
            ),
            'installation', json_build_object(
                'installation_id', inst.installation_no,
                'installation_type_name', inst_type.name,
                'installation_type', inst_type.code,
                'cpe_type', cpe.code,
                'installation_date', inst.installation_date,
                'installation_slot', tslot.name
            ),
            'customer_info', json_build_object(
                'name', CASE WHEN od.new_customer_name IS NOT NULL THEN od.new_customer_name ELSE rp.name END,
                'phone', pf.personal_phone,
                'mobile', pf.personal_mobile,
                'other_phone', pf.other_phone,
                'email', pf.personal_email,
                'partner_code', CASE WHEN od.customer IS NOT NULL THEN ptnr_personal.sync_code WHEN od.customer_id IS NOT NULL THEN cust_personal.sync_code ELSE '' END,
                'customer_id', od.customer_id,
                'customer_type', CASE WHEN od.customer IS NOT NULL THEN st.name WHEN od.customer_id IS NOT NULL THEN cust_st.name ELSE NULL END,
                'is_blacklisted', CASE WHEN od.blacklist_status = 'BLACKLIST' THEN true ELSE false END,
                'personal_info', json_build_object(
                    'national', pn.name,
                    'nrc_type', pf.nrc_type,
                    'nrc', json_build_object(
                        'nrc_first_number_code', nfn.name,
                        'nrc_township_code', ntc.name,
                        'nrc_register_code', nrc.name,
                        'nrc_number', pf.nrc_no
                    ),
                    'other_nrc', pf.other_id,
                    'passport', pf.passport
                )
            ),
            'address_info', json_build_object(
                'country_code', CASE WHEN od.is_same_with_billing_address = true THEN rc.country_code ELSE src.country_code END,
                'state_code', CASE WHEN od.is_same_with_billing_address = true THEN cs.state_code ELSE scs.state_code END,
                'city_code', CASE WHEN od.is_same_with_billing_address = true THEN city.city_code ELSE scity.city_code END,
                'township_code', CASE WHEN od.is_same_with_billing_address = true THEN town.township_code ELSE stown.township_code END,
                'ward_code', CASE WHEN od.is_same_with_billing_address = true THEN ward.ward_code ELSE sward.ward_code END,
                'street_code', CASE WHEN od.is_same_with_billing_address = true THEN street.street_code ELSE sstreet.street_code END,
                'building_no', CASE WHEN od.is_same_with_billing_address = true THEN fd.building_no ELSE od.service_building_no END,
                'unit', CASE WHEN od.is_same_with_billing_address = true THEN fd.unit ELSE od.service_unit END,
                'room_no', CASE WHEN od.is_same_with_billing_address = true THEN fd.room_no ELSE od.service_room_no END,
                'floor', CASE WHEN od.is_same_with_billing_address = true THEN fd.floor ELSE od.service_floor END,
                'housing_code', CASE WHEN od.is_same_with_billing_address = true THEN NULL ELSE shouse.housing_code END,
                'block', CASE WHEN od.is_same_with_billing_address = true THEN fd.block ELSE od.service_block END,
                'cross_street', CASE WHEN od.is_same_with_billing_address = true THEN fd.cross_street ELSE od.service_cross_street END,
                'latitude', CASE WHEN od.is_same_with_billing_address = true THEN fd.latitude ELSE od.service_latitude END,
                'longitude', CASE WHEN od.is_same_with_billing_address = true THEN fd.longitude ELSE od.service_longitude END
            )
        ) AS result
        FROM frnt_order_order od
        LEFT JOIN frnt_order_type otype ON otype.id = od.order_type
        LEFT JOIN frnt_service_type ser ON ser.id = od.service_type
        LEFT JOIN frnt_subscription_package_bundle pack ON pack.id = od.package_bundle
        LEFT JOIN frnt_address_opi opi ON opi.id = od.opi_id
        LEFT JOIN frnt_installation_installation inst ON inst.id = od.installation
        LEFT JOIN frnt_installation_installation_type inst_type ON inst_type.id = inst.installation_type
        LEFT JOIN frnt_installation_cpe_type cpe ON cpe.id = inst.cpe_type
        LEFT JOIN frnt_installation_time_slot tslot ON tslot.id = inst.installation_time_slot
        LEFT JOIN res_partner rp ON rp.id = od.customer
        LEFT JOIN frnt_partner_partner_personal ptnr_personal ON ptnr_personal.partner_id = rp.id
        LEFT JOIN frnt_service_type st ON rp.customer_type_id = st.id
        LEFT JOIN res_partner customer ON customer.customer_id = od.customer_id
        LEFT JOIN frnt_partner_partner_personal cust_personal ON cust_personal.partner_id = customer.id
        LEFT JOIN frnt_service_type cust_st ON customer.customer_type_id = cust_st.id
        LEFT JOIN frnt_personal_info_personal_info pf ON pf.id = od.personal_info
        LEFT JOIN partner_nationality pn ON pn.id = pf.national_id
        LEFT JOIN nrc_first_number nfn ON nfn.id = pf.nrc_first_no_id
        LEFT JOIN nrc_township_code ntc ON ntc.id = pf.nrc_township_code_id
        LEFT JOIN nrc_register_code nrc ON nrc.id = pf.nrc_register_code
        LEFT JOIN frnt_address_frnt_address fd ON fd.id = od.billing_address
        LEFT JOIN res_country rc ON rc.id = fd.res_country_id
        LEFT JOIN res_country_state cs ON cs.id = fd.res_state_id
        LEFT JOIN res_city city ON city.id = fd.res_city_id
        LEFT JOIN res_district_township town ON town.id = fd.res_township_id
        LEFT JOIN res_town_ward ward ON ward.id = fd.res_ward_id
        LEFT JOIN res_street_name street ON street.id = fd.street_name_id
        LEFT JOIN res_housing_name house ON house.id = fd.housing_id
        LEFT JOIN res_country src ON src.id = od.service_country_id
        LEFT JOIN res_country_state scs ON scs.id = od.service_state_id
        LEFT JOIN res_city scity ON scity.id = od.service_city_id
        LEFT JOIN res_district_township stown ON stown.id = od.service_township_id
        LEFT JOIN res_town_ward sward ON sward.id = od.service_ward_id
        LEFT JOIN res_street_name sstreet ON sstreet.id = od.service_street_name_id
        LEFT JOIN res_housing_name shouse ON shouse.id = od.service_housing_id
        WHERE od.billing_address IS NOT NULL AND od.order_id = $1
        ORDER BY od.id DESC;
"""

    ORDER_LIST_QUERY = """
        SELECT json_build_object(
            'poi', od.order_id,
            'order_type', otype.name,
            'status', od.state,
            'service', json_build_object(
                'service_type', ser.name,
                'OPI', COALESCE(opi.code, ''),
                'package', pack.name,
                'price', od.price
            ),
            'installation', json_build_object(
                'installation_id', inst.installation_no,
                'installation_type_name', inst_type.name,
                'installation_type', inst_type.code,
                'cpe_type', cpe.code,
                'installation_date', inst.installation_date,
                'installation_slot', tslot.name
            ),
            'customer_info', json_build_object(
                'name', CASE WHEN od.new_customer_name IS NOT NULL THEN od.new_customer_name ELSE rp.name END,
                'phone', pf.personal_phone,
                'mobile', pf.personal_mobile,
                'other_phone', pf.other_phone,
                'email', pf.personal_email,
                'partner_code', CASE WHEN od.customer IS NOT NULL THEN ptnr_personal.sync_code WHEN od.customer_id IS NOT NULL THEN cust_personal.sync_code ELSE '' END,
                'customer_id', od.customer_id,
                'customer_type', CASE WHEN od.customer IS NOT NULL THEN st.name WHEN od.customer_id IS NOT NULL THEN cust_st.name ELSE NULL END,
                'is_blacklisted', CASE WHEN od.blacklist_status = 'BLACKLIST' THEN true ELSE false END,
                'personal_info', json_build_object(
                    'national', pn.name,
                    'nrc_type', pf.nrc_type,
                    'nrc', json_build_object(
                        'nrc_first_number_code', nfn.name,
                        'nrc_township_code', ntc.name,
                        'nrc_register_code', nrc.name,
                        'nrc_number', pf.nrc_no
                    ),
                    'other_nrc', pf.other_id,
                    'passport', pf.passport
                )
            ),
            'address_info', json_build_object(
                'country_code', CASE WHEN od.is_same_with_billing_address = true THEN rc.country_code ELSE src.country_code END,
                'state_code', CASE WHEN od.is_same_with_billing_address = true THEN cs.state_code ELSE scs.state_code END,
                'city_code', CASE WHEN od.is_same_with_billing_address = true THEN city.city_code ELSE scity.city_code END,
                'township_code', CASE WHEN od.is_same_with_billing_address = true THEN town.township_code ELSE stown.township_code END,
                'ward_code', CASE WHEN od.is_same_with_billing_address = true THEN ward.ward_code ELSE sward.ward_code END,
                'street_code', CASE WHEN od.is_same_with_billing_address = true THEN street.street_code ELSE sstreet.street_code END,
                'building_no', CASE WHEN od.is_same_with_billing_address = true THEN fd.building_no ELSE od.service_building_no END,
                'unit', CASE WHEN od.is_same_with_billing_address = true THEN fd.unit ELSE od.service_unit END,
                'floor', CASE WHEN od.is_same_with_billing_address = true THEN fd.floor ELSE od.service_floor END,
                'housing_code', CASE WHEN od.is_same_with_billing_address = true THEN NULL ELSE shouse.housing_code END,
                'block', CASE WHEN od.is_same_with_billing_address = true THEN fd.block ELSE od.service_block END,
                'cross_street', CASE WHEN od.is_same_with_billing_address = true THEN fd.cross_street ELSE od.service_cross_street END,
                'latitude', CASE WHEN od.is_same_with_billing_address = true THEN fd.latitude ELSE od.service_latitude END,
                'longitude', CASE WHEN od.is_same_with_billing_address = true THEN fd.longitude ELSE od.service_longitude END
            )
        ) AS result
        FROM frnt_order_order od
        LEFT JOIN frnt_order_type otype ON otype.id = od.order_type
        LEFT JOIN frnt_service_type ser ON ser.id = od.service_type
        LEFT JOIN frnt_subscription_package_bundle pack ON pack.id = od.package_bundle
        LEFT JOIN frnt_address_opi opi ON opi.id = od.opi_id
        LEFT JOIN frnt_installation_installation inst ON inst.id = od.installation
        LEFT JOIN frnt_installation_installation_type inst_type ON inst_type.id = inst.installation_type
        LEFT JOIN frnt_installation_cpe_type cpe ON cpe.id = inst.cpe_type
        LEFT JOIN frnt_installation_time_slot tslot ON tslot.id = inst.installation_time_slot
        LEFT JOIN res_partner rp ON rp.id = od.customer
        LEFT JOIN frnt_partner_partner_personal ptnr_personal ON ptnr_personal.partner_id = rp.id
        LEFT JOIN frnt_service_type st ON rp.customer_type_id = st.id
        LEFT JOIN res_partner customer ON customer.customer_id = od.customer_id
        LEFT JOIN frnt_partner_partner_personal cust_personal ON cust_personal.partner_id = customer.id
        LEFT JOIN frnt_service_type cust_st ON customer.customer_type_id = cust_st.id
        LEFT JOIN frnt_personal_info_personal_info pf ON pf.id = od.personal_info
        LEFT JOIN partner_nationality pn ON pn.id = pf.national_id
        LEFT JOIN nrc_first_number nfn ON nfn.id = pf.nrc_first_no_id
        LEFT JOIN nrc_township_code ntc ON ntc.id = pf.nrc_township_code_id
        LEFT JOIN nrc_register_code nrc ON nrc.id = pf.nrc_register_code
        LEFT JOIN frnt_address_frnt_address fd ON fd.id = od.billing_address
        LEFT JOIN res_country rc ON rc.id = fd.res_country_id
        LEFT JOIN res_country_state cs ON cs.id = fd.res_state_id
        LEFT JOIN res_city city ON city.id = fd.res_city_id
        LEFT JOIN res_district_township town ON town.id = fd.res_township_id
        LEFT JOIN res_town_ward ward ON ward.id = fd.res_ward_id
        LEFT JOIN res_street_name street ON street.id = fd.street_name_id
        LEFT JOIN res_housing_name house ON house.id = fd.housing_id
        LEFT JOIN res_country src ON src.id = od.service_country_id
        LEFT JOIN res_country_state scs ON scs.id = od.service_state_id
        LEFT JOIN res_city scity ON scity.id = od.service_city_id
        LEFT JOIN res_district_township stown ON stown.id = od.service_township_id
        LEFT JOIN res_town_ward sward ON sward.id = od.service_ward_id
        LEFT JOIN res_street_name sstreet ON sstreet.id = od.service_street_name_id
        LEFT JOIN res_housing_name shouse ON shouse.id = od.service_housing_id
        WHERE od.billing_address IS NOT NULL
        AND LOWER(od.state) = LOWER($1) AND LOWER(otype.name) = $2 AND od.order_date BETWEEN $3 AND $4
        ORDER BY od.id DESC LIMIT 1;
"""

    DETAIL_QUERY = """
    SELECT
    po.new_customer_name AS name,
    po.employee_id AS employee_id,
    po.biz_registration_no AS biz_reg_no,
    po.order_id AS poi,
    po.order_date,
    po.state AS status,
    ot.name AS order_type_name,
    ot.code AS order_type_code,
    po.blacklist_status,
    po.billing_address AS billing_address_id,
    po.installation AS installation_table_id,
    po.is_same_with_billing_address,

    po.customer_id,
    pp.sync_code AS partner_code,
    po.create_date,
    po.write_date,

    -- Service INFO
    st.id AS service_type_id,
    st.name AS service_type_name,
    st.code AS service_type_code,
    pkg.id AS package_id,
    pkg.name AS package_name,
    pkg.code AS package_code,
    po.group_ref_id AS group_ref_id,
    opi.name AS opi_name,
    opi.code AS opi_code,

    -- Personal_info
    fpfp.personal_phone AS phone,
    fpfp.personal_mobile AS mobile,
    fpfp.other_phone AS other_phone,
    fpfp.personal_email AS email,
    pn.name AS national,
    fpfp.nrc_type AS nrc_type,
    nfn.nrc_first_number_code AS nrc_first_number_code,
    nrc_tsp.nrc_township_code AS nrc_township_code,
    nrc_reg.nrc_register_code AS nrc_register_code,
    fpfp.nrc_no AS nrc_number,

    fpfp.other_id AS other_nrc,
    fpfp.passport AS passport,
    fpfp.date_of_birth AS date_of_birth,
    fpfp.live_type AS live_type

    FROM frnt_order_order AS po
    LEFT JOIN frnt_order_type AS ot ON ot.id=po.order_type
    LEFT JOIN frnt_service_type AS st ON st.id=po.service_type
    LEFT JOIN frnt_subscription_package_bundle AS pkg ON pkg.id=po.package_bundle
    LEFT JOIN frnt_address_opi AS opi ON opi.id=po.opi_id
    LEFT JOIN res_partner AS rp ON rp.id=po.customer
    LEFT JOIN frnt_partner_partner_personal AS pp ON pp.partner_id=rp.id
    LEFT JOIN frnt_personal_info_personal_info AS fpfp ON fpfp.id=po.personal_info
    LEFT JOIN partner_nationality AS pn ON pn.id=fpfp.national_id
    LEFT JOIN nrc_first_number nfn ON nfn.id=fpfp.nrc_first_no_id
    LEFT JOIN nrc_township_code nrc_tsp ON nrc_tsp.id=fpfp.nrc_township_code_id
    LEFT JOIN nrc_register_code nrc_reg ON nrc_reg.id=fpfp.nrc_register_code
    """

    DETAIL_BILLING_ADDRESS = """
    SELECT

    rc.name AS country_name,
    rc.country_code AS country_code,
    --
    rcs.name AS state_name,
    rcs.state_code AS state_code,
    --
    rct.name AS city_name,
    rct.city_code AS city_code,
    --
    ts.name AS township_name,
    ts.township_code AS township_code,
    --
    rtw.name AS ward_name,
    rtw.ward_code AS ward_code,
    --
    street.name AS street_name,
    street.street_code AS street_code,
    --
    house.name AS housing_name,
    house.housing_code AS housing_code,
    --
    bt.name AS billing_township_name,
    bt.billing_township_code AS billing_township_code,
    --
    addr.building_no AS building_no,
    addr.unit AS unit,
    addr.room_no AS room_no,
    addr.floor AS floor,
    addr.block AS block,
    addr.cross_street AS cross_street,
    addr.billing_zone AS billing_zone,
    addr.latitude AS latitude,
    addr.longitude AS longitude

    FROM frnt_address_frnt_address AS addr
    LEFT JOIN res_country rc ON rc.id = addr.res_country_id
    LEFT JOIN res_country_state rcs ON rcs.id = addr.res_state_id
    LEFT JOIN res_city rct ON rct.id = addr.res_city_id
    LEFT JOIN res_district_township ts ON ts.id = addr.res_township_id
    LEFT JOIN res_town_ward rtw ON rtw.id = addr.res_ward_id
    LEFT JOIN res_street_name street ON street.id = addr.street_name_id
    LEFT JOIN res_housing_name house ON house.id = addr.housing_id
    LEFT JOIN billing_township bt ON bt.id=addr.billing_township_id
    WHERE addr.id=$1
    """

    DETAIL_SERVICE_ADDRESS = """
    SELECT

    rc.name AS country_name,
    rc.country_code AS country_code,
    --
    rcs.name AS state_name,
    rcs.state_code AS state_code,
    --
    rct.name AS city_name,
    rct.city_code AS city_code,
    --
    ts.name AS township_name,
    ts.township_code AS township_code,
    --
    rtw.name AS ward_name,
    rtw.ward_code AS ward_code,
    --
    street.name AS street_name,
    street.street_code AS street_code,
    --
    house.name AS housing_name,
    house.housing_code AS housing_code,
    --
    '' AS billing_township_name,
    '' AS billing_township_code,
    --
    po.service_building_no AS building_no,
    po.service_unit AS unit,
    po.service_room_no AS room_no,
    po.service_floor AS floor,
    po.service_block AS block,
    po.service_cross_street AS cross_street,
    '' AS billing_zone,
    po.service_latitude AS latitude,
    po.service_longitude AS longitude

    FROM frnt_order_order AS po
    LEFT JOIN res_country rc ON rc.id = po.service_country_id
    LEFT JOIN res_country_state rcs ON rcs.id = po.service_state_id
    LEFT JOIN res_city rct ON rct.id = po.service_city_id
    LEFT JOIN res_district_township ts ON ts.id = po.service_township_id
    LEFT JOIN res_town_ward rtw ON rtw.id = po.service_ward_id
    LEFT JOIN res_street_name street ON street.id = po.service_street_name_id
    LEFT JOIN res_housing_name house ON house.id = po.service_housing_id
    WHERE po.order_id=$1
    """

    DETAIL_INSTALLTION = """
    SELECT

    inst.cpe AS cid,
    inst.installation_no AS installation_id,
    inst.installation_date,
    inst.installation_done_date,
    it.id AS installation_type_id,
    it.name AS installation_type_name,
    it.code AS installation_type_code,
    ct.name AS cpe_type_name,
    ct.code AS cpe_type_code,
    sit.name AS subscribed_installation_type_name,
    sit.code AS subscribed_installation_type_code,
    inst.create_date,
    inst.write_date,
    ic.name AS installation_category,
    inst.state AS status

    FROM frnt_installation_installation AS inst
    LEFT JOIN frnt_installation_cpe_type AS ct ON ct.id=inst.cpe_type
    LEFT JOIN frnt_installation_installation_type AS it ON it.id=inst.installation_type
    LEFT JOIN frnt_installation_installation_category AS ic ON ic.code=it.category
    LEFT JOIN frnt_installation_installation_type AS sit ON sit.id=inst.subscribed_installation_type
    WHERE inst.id=$1
    """

    DETAIL_TAPSIN = """

    """

    DETAIL_WHERE_CLAUSE = """
    WHERE po.order_id=$1
    """

    INFO_QUERY = """
    SELECT

    po.order_id AS id,
    po.order_id AS poi,
    ot.name AS order_type_name,
    po.order_date,
    po.state AS status,
    po.new_customer_name,
    rp.name AS customer_name,
    pp.sync_code AS partner_code,
    rp.customer_id,
    fst.name AS service_type_name,
    pkg.name AS package_name,
    inst.installation_no AS installation_id,
    inst_type.name AS installation_type_name
    """

    COMMON_QUERY = """
    FROM frnt_order_order AS po
    LEFT JOIN frnt_order_type ot ON ot.id=po.order_type
    LEFT JOIN res_partner AS rp ON rp.id=po.customer
    LEFT JOIN frnt_partner_partner_personal AS pp ON pp.partner_id=po.customer
    LEFT JOIN frnt_service_type AS fst ON fst.id=po.service_type
    LEFT JOIN frnt_subscription_package_bundle AS pkg ON pkg.id=po.package_bundle
    LEFT JOIN frnt_installation_installation AS inst ON inst.id=po.installation
    LEFT JOIN frnt_installation_installation_type AS inst_type ON inst_type.id=inst.installation_type
    {filter}
    {sort}
    {range}
    """
