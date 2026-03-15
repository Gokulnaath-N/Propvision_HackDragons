import requests
import json
import os

BASE = "http://localhost:8000"

def debug_search():
    try:
        r = requests.post(f"{BASE}/search", json={"query": "bedroom with natural light"})
        data = {
            "status_code": r.status_code,
            "response": r.json()
        }
        with open("search_debug_final.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print("Wrote search_debug_final.json")
    except Exception as e:
        with open("search_debug_final.json", "w", encoding="utf-8") as f:
            json.dump({"error": str(e)}, f, indent=2)
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_search()
