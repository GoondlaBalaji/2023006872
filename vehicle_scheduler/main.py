import os
import sys
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ensure logging_middleware is accessible
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logging_middleware.app.config import ACCESS_TOKEN, BASE_URL
from logging_middleware.app.logger import Log

def solve_knapsack(capacity, items):
    # items is a list of dicts: {'TaskID': ..., 'Duration': ..., 'Impact': ...}
    n = len(items)
    dp = [[0 for _ in range(capacity + 1)] for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        for w in range(1, capacity + 1):
            weight = items[i-1]['Duration']
            value = items[i-1]['Impact']
            
            if weight <= w:
                dp[i][w] = max(value + dp[i-1][w-weight], dp[i-1][w])
            else:
                dp[i][w] = dp[i-1][w]
                
    # Backtrack to find selected items
    res = dp[n][capacity]
    w = capacity
    selected_items = []
    
    for i in range(n, 0, -1):
        if res <= 0:
            break
        if res == dp[i-1][w]:
            continue
        else:
            selected_items.append(items[i-1])
            res -= items[i-1]['Impact']
            w -= items[i-1]['Duration']
            
    return selected_items, dp[n][capacity]


def get_schedule():
    Log("backend", "info", "service", "Starting Vehicle Maintenance Scheduler")
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    
    try:
        depots_response = requests.get(f"{BASE_URL}/depots", headers=headers, verify=False)
        depots_response.raise_for_status()
        depots = depots_response.json().get('depots', [])
        Log("backend", "info", "service", f"Successfully fetched {len(depots)} depots")
    except Exception as e:
        Log("backend", "error", "service", f"Failed to fetch depots: {str(e)[:20]}")
        return {"error": str(e)}

    try:
        vehicles_response = requests.get(f"{BASE_URL}/vehicles", headers=headers, verify=False)
        vehicles_response.raise_for_status()
        vehicles = vehicles_response.json().get('vehicles', [])
        Log("backend", "info", "service", f"Successfully fetched {len(vehicles)} vehicles")
    except Exception as e:
        Log("backend", "error", "service", f"Failed to fetch vehicles: {str(e)[:20]}")
        return {"error": str(e)}
        
    results = []
    
    for depot in depots:
        depot_id = depot['ID']
        budget = depot['MechanicHours']
        
        selected_vehicles, total_impact = solve_knapsack(budget, vehicles)
        total_duration = sum(v['Duration'] for v in selected_vehicles)
        
        results.append({
            "depot_id": depot_id,
            "mechanic_hours_budget": budget,
            "total_duration": total_duration,
            "total_impact": total_impact,
            "scheduled_vehicles": selected_vehicles
        })
            
        Log("backend", "info", "service", f"Depot {depot_id}: {len(selected_vehicles)} vehicles, score {total_impact}")
        
    Log("backend", "info", "service", "Scheduler completed")
    return {"status": "success", "data": results}

if __name__ == "__main__":
    print(get_schedule())
