import json
import os

# Read configurations from a config file
with open("config.json") as config_file:
    configsDict = json.load(config_file)

iam_realm_name = configsDict["iam_realm_name"]
iam_realm_admin_username = configsDict["iam_realm_admin_username"]
iam_realm_admin_password = configsDict["iam_realm_admin_password"]
iam_client_name = configsDict["iam_client_name"]
iam_client_role_name = configsDict["iam_client_role_name"]
iam_master_token_url = configsDict["iam_master_token_url"]
iam_realms_url = configsDict["iam_realms_url"]
