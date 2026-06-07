import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://4.224.186.213/evaluation-service"

def get_access_token():
    payload = {
        "email": "bgoondla@gitam.in",
        "name": "goondla balaji",
        "rollNo": "2023006872",
        "accessCode": "wgKtgZ",
        "clientID": "1d65483f-09a0-41a8-93af-7b9f05c855a0",
        "clientSecret": "BPGKrfPMsHymTjUw"
    }
    response = requests.post(
        f"{BASE_URL}/auth",
        json=payload,
        verify=False
    )
    if response.status_code in [200, 201]:
        return response.json().get("access_token")
    return None

ACCESS_TOKEN = get_access_token()