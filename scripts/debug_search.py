import requests
import json

BASE = "http://localhost:8000"

def debug_search():
    print("DEBUG SEARCH ENDPOINT")
    try:
        r = requests.post(f"{BASE}/search", json={"query": "bedroom with natural light"})
        print(f"Status Code: {r.status_code}")
        print("Response Content:")
        print(json.dumps(r.json(), indent=2))
    except Exception as e:
        print(f"Error making request: {e}")

if __name__ == "__main__":
    debug_search()
