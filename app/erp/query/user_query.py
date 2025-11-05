class UserQuery:
    user_login = """
        SELECT id,login FROM res_users WHERE login = $1;
    """
