import requests
import json
import configs


token = ""


def log_response(message, response):
    print(
        "==============================        "
        + message
        + "        =============================="
    )
    print(response.status_code)
    print(response.headers)
    print(response.raw)


def log_request(message, url):
    print(
        "==============================        "
        + message
        + "        =============================="
    )
    print(url)


def get_token_url(realm_name):
    return configs.iam_master_token_url.replace("master", realm_name)


def get_access_token():
    url = configs.iam_master_token_url
    dataDict = {
        "client_id": "admin-cli",
        "grant_type": "password",
        "username": "keycloak",
        "password": "keycloak",
    }
    response = requests.post(url, data=dataDict)
    token = response.json().get("access_token")
    return token


def login_to_realm(realm_name, client_name, client_secret, username, password):
    url = get_token_url(realm_name)
    dataDict = {
        "client_id": client_name,
        "client_secret": client_secret,
        "grant_type": "password",
        "username": username,
        "password": password,
    }
    response = requests.post(url, data=dataDict)
    return response.json().get("access_token")


def create_request_header():
    global token
    if not token:
        token = get_access_token()
    bearer = "Bearer " + token
    req_headers = {"Authorization": bearer, "Content-Type": "application/json"}
    return req_headers


def create_realm(realm_name):
    url = configs.iam_realms_url
    data = {"realm": realm_name, "enabled": True}
    response = requests.post(url, json=data, headers=create_request_header())
    log_response("create_realm response:", response)


def create_admin_for_realm(realm_name, realm_admin_username, iam_realm_admin_password):
    url = configs.iam_realms_url + "/" + realm_name + "/users"
    data = {
        "username": realm_admin_username,
        "enabled": True,
        "credentials": [
            {"type": "password", "value": iam_realm_admin_password, "temporary": False}
        ],
    }
    response = requests.post(url, json=data, headers=create_request_header())
    log_response("create_admin_for_realm response:", response)
    user_uri = response.headers[
        "Location"
    ]  # e.g. http://localhost:8080/auth/admin/realms/nosy-realm/users/d1131ab4-a6ef-4e6a-9501-b44874059162
    return user_uri.split("/")[
        -1
    ]  # grabs only last part (i.e d1131ab4-a6ef-4e6a-9501-b44874059162) which is user id


def create_client_for_realm(realm_name, client_name):
    url = configs.iam_realms_url + "/" + realm_name + "/clients"
    data = {
        "clientId": client_name,
        "name": client_name,
        "enabled": True,
        "bearerOnly": False,
        "standardFlowEnabled": True,
        "directAccessGrantsEnabled": True,
        "publicClient": False,
        "protocol": "openid-connect",
        "access": {"view": True, "configure": True, "manage": True},
    }
    response = requests.post(url, json=data, headers=create_request_header())
    log_response("create_client_for_realm response:", response)
    '''
    keycloak returns a "Location" field in response header after creating a resource.
    This location is URL to the created resource and will look something like:
    http://localhost:8080/auth/admin/realms/nosy-realm/clients/69f1cda7-6305-41c0-bc28-31c28c62ac11
    So to get the resource ID, we should pick the last part of the URL, after last slash
    '''
    client_uri = response.headers["Location"]
    # grabs and return only last part (i.e. 69f1cda7-6305-41c0-bc28-31c28c62ac11) which is client id:
    return client_uri.split("/")[-1]

def add_client_role(realm_name, client_id, role_name):
    url = configs.iam_realms_url + "/" + realm_name + "/clients/" + client_id + "/roles"
    data = {
        "name": role_name,
        "description": "${"+role_name+"}",
        "composite": False,
        "clientRole": True
    }
    requests.post(url, json=data, headers=create_request_header())


def get_client_id(realm_name, client_name):
    # get all clients with name realm-management
    url = configs.iam_realms_url + "/" + realm_name + "/clients?clientId=" + client_name
    response = requests.get(url, headers=create_request_header())
    # return first item's id
    return response.json()[0]["id"]


def assign_client_roles_to_realm_admin(realm_name, client_id, realm_admin_id):
    user_roles = []
    realm_url = configs.iam_realms_url + "/" + realm_name
    # 1. get client roles for client_name and realm-management client
    # e.g. http://localhost:8080/auth/admin/realms/nosy-realm/clients/85884317-2080-496c-b1ba-89e2d0a89956/roles

    get_client_roles_url = realm_url + "/clients/" + client_id + "/roles"
    log_request("assign_client_roles_to_realm_admin req:", get_client_roles_url)
    response = requests.get(get_client_roles_url, headers=create_request_header())
    log_response("assign_client_roles_to_realm_admin response:", response)
    client_roles = response.json()
    for r in client_roles:
        user_roles.append({"id": r["id"], "name": r["name"]})

    # 2. add all of them to user's client roles
    # post http://localhost:8080/auth/admin/realms/tt/users/{user_id}/role-mappings/clients/{client_id}
    assign_roles_to_user_url = (
        realm_url + "/users/" + realm_admin_id + "/role-mappings/clients/" + client_id
    )
    requests.post(
        assign_roles_to_user_url, json=user_roles, headers=create_request_header()
    )


def get_client_secret(realm_name, client_id):
    """
    req:
    GET http://localhost:8080/auth/admin/realms/tt/clients/85884317-2080-496c-b1ba-89e2d0a89956/client-secret
    res:
    {
        "type": "secret",
        "value": "4294f4e8-e293-4967-a0c1-fc53be406d57"
    }
    """
    url = (
        configs.iam_realms_url
        + "/"
        + realm_name
        + "/clients/"
        + client_id
        + "/client-secret"
    )
    log_request("get_client_secret req:", url)
    response = requests.get(url, headers=create_request_header())
    log_response("get_client_secret response:", response)
    return response.json()["value"]


def get_realm_users(realm_name, realm_admin_token):
    # GET http://localhost:8080/auth/admin/realms/tt/users
    url = configs.iam_realms_url + "/" + realm_name + "/users"
    log_request("get_realm_users req:", url)
    print("realm_admin_token " + realm_admin_token)
    bearer = "Bearer " + realm_admin_token
    req_headers = {"Authorization": bearer, "Content-Type": "application/json"}
    response = requests.get(url, headers=req_headers)
    log_response("get_realm_users response:", response)
    return response.json()
