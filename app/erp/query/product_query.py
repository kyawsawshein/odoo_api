class ProductQuery:
    get_product = """
        SELECT      pp.id,pt.name,pt.list_price
        FROM        product_product pp
        INNER JOIN  product_template pt ON pt.id=pp.product_tmpl_id
        INNER JOIN  product_category pc ON pt.categ_id = pc.id
        WHERE	    pc.name = 'Printed'
        LIMIT       $1;
    """
