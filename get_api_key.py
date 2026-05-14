import os
import json
from google.oauth2 import service_account
from google.cloud import api_keys_v2

# Load credentials from backend/.env
env_file = "backend/.env"
creds_json_str = None
with open(env_file, "r") as f:
    for line in f:
        if line.startswith("GOOGLE_APPLICATION_CREDENTIALS_JSON="):
            creds_json_str = line.split("=", 1)[1].strip()
            break

if creds_json_str:
    creds_dict = json.loads(creds_json_str)
    credentials = service_account.Credentials.from_service_account_info(creds_dict)
    
    client = api_keys_v2.ApiKeysClient(credentials=credentials)
    project_id = creds_dict["project_id"]
    
    try:
        request = api_keys_v2.ListKeysRequest(
            parent=f"projects/{project_id}/locations/global",
        )
        page_result = client.list_keys(request=request)
        for response in page_result:
            print(f"Key name: {response.name}")
            print(f"Display name: {response.display_name}")
            
            # Get key string
            key_req = api_keys_v2.GetKeyStringRequest(name=response.name)
            key_str = client.get_key_string(request=key_req)
            print(f"Key string: {key_str.key_string}\n")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("Credentials not found")
