import os
import sys
import requests
import urllib3
import heapq
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ensure logging_middleware is accessible
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logging_middleware.app.config import ACCESS_TOKEN, BASE_URL
from logging_middleware.app.logger import Log

def get_priority_weight(notif_type):
    # Placement > Result > Event
    weights = {
        "Placement": 3,
        "Result": 2,
        "Event": 1
    }
    return weights.get(notif_type, 0)

def get_top_notifications():
    Log("backend", "info", "service", "Starting Priority Inbox")
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/notifications", headers=headers, verify=False)
        response.raise_for_status()
        notifications = response.json().get('notifications', [])
        Log("backend", "info", "service", f"Fetched {len(notifications)} notifs")
    except Exception as e:
        Log("backend", "error", "service", f"Failed to fetch notifs: {str(e)[:20]}")
        return {"error": str(e)}

    # Min-heap to maintain top 10 notifications
    top_notifications = []
    
    for notif in notifications:
        notif_id = notif['ID']
        notif_type = notif['Type']
        message = notif['Message']
        timestamp_str = notif['Timestamp']
        
        weight = get_priority_weight(notif_type)
        # Parse timestamp to datetime for recency comparison
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        
        # Tuple for comparison: (weight, timestamp, notif_id)
        heap_item = (weight, timestamp, notif_id, notif)
        
        if len(top_notifications) < 10:
            heapq.heappush(top_notifications, heap_item)
        else:
            if heap_item > top_notifications[0]:
                heapq.heapreplace(top_notifications, heap_item)
                
    # Sort the top 10 in descending order for display
    top_notifications.sort(key=lambda x: (x[0], x[1]), reverse=True)
    
    results = []
    for idx, item in enumerate(top_notifications, start=1):
        weight, timestamp, notif_id, notif = item
        results.append(notif)
        
    Log("backend", "info", "service", "Priority Inbox processed successfully")
    return {"status": "success", "top_10_notifications": results}

if __name__ == "__main__":
    print(get_top_notifications())
