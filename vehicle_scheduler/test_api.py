# vehicle_scheduler/test_api.py

import requests
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logging_middleware.app.config import ACCESS_TOKEN

TOKEN = ACCESS_TOKEN

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

depots = requests.get(
    "https://4.224.186.213/evaluation-service/depots",
    headers=headers,
    verify=False
)

vehicles = requests.get(
    "https://4.224.186.213/evaluation-service/vehicles",
    headers=headers,
    verify=False
)

print(depots.json())
print(vehicles.json())