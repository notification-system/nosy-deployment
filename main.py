import iam
import configs


def main():
    
    realm_name = configs.iam_realm_name
    
    # 1 - authenticate with root user
    print(iam.get_access_token())

    # 2 - create realm
    iam.create_realm(realm_name)

    # 3 - create admin user for realm with initial password and make it enabled
    admin_id = iam.create_admin_for_realm(
        realm_name, configs.iam_realm_admin_username, configs.iam_realm_admin_password
    )

    # 4 - create a client in realm with some initial important fields
    client_id = iam.create_client_for_realm(realm_name, configs.iam_client_name)

    # 5 - add a role to client
    iam.add_client_role(realm_name, client_id, configs.iam_client_role_name)

    # 6 - assign client roles to realm admin
    iam.assign_client_roles_to_realm_admin(realm_name, client_id, admin_id)

    # 7 - assign realm-management client roles to realm admin
    iam.assign_client_roles_to_realm_admin(
        realm_name, iam.get_client_id(realm_name, "realm-management"), admin_id
    )

    # !!! from here, everything is for test sake and is not actually creatig or configuring anything

    # 8 - get client secret
    client_secret = iam.get_client_secret(realm_name, client_id)
    print("got client secret: " + client_secret)

    # 9 - login with admin, client-id and secret to the realm
    realm_admin_token = iam.login_to_realm(
        realm_name,
        configs.iam_client_name,
        client_secret,
        configs.iam_realm_admin_username,
        configs.iam_realm_admin_password,
    )
    print("got realm_admin_token: " + realm_admin_token)

    # 10 - get user list in realm (to check if admin has correct permissions)
    users = iam.get_realm_users(realm_name, realm_admin_token)

    print("got realm users: ")
    print(users)


main()
