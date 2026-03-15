import requests
import json

try:
    r = requests.get("http://localhost:8000/debug/env")
    print(json.dumps(r.json(), indent=2))
except Exception as e:
    print(f"Failed to reach debug endpoint: {e}")
