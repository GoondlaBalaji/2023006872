import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from .config import ACCESS_TOKEN, BASE_URL


def Log(stack, level, package, message):

    response = requests.post(
        f"{BASE_URL}/logs",
        headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "stack": stack,
            "level": level,
            "package": package,
            "message": message
        },
        verify=False,
        timeout=15
    )

    print("Status:", response.status_code)
    print("Response:", response.text)

    return response.json()