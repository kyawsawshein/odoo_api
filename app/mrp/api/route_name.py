class Route:
    orders = "/order"
    order_id = "/order/{order_id}"
    order_workorder = "/{order_id}/workorder"
    workorders = "/workorder"
    workorder_id = "/workorder/{work_id}"
    start_workorder = "/workorder/{work_id}/start"
    pending_workorder = "/workorder/{work_id}/pending"
    end_workorder = "/workorder/{work_id}/end"
