class CustomerQuery:
    get_customers = """
        SELECT id,customer_id,name FROM res_partner WHERE customer_rank > 0 LIMIT $1;
    """

    get_customer_check = """
        SELECT id,customer_id,name FROM res_partner WHERE customer_id = $1;
    """
