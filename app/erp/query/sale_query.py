class SaleQuery:
    get_user_id = """
        SELECT id,name FROM sale_order WHERE name=$1;
    """
