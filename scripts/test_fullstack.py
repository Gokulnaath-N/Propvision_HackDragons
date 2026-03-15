import requests
import json

BASE = "http://localhost:8000"

def test_all():
  print("PROPVISION AI - FULL STACK TEST")
  print("=" * 40)
  
  # 1. Health
  r = requests.get(f"{BASE}/health")
  assert r.status_code == 200
  print(f"GET  /health          {r.status_code} OK")
  
  # 2. Search (what SearchInterface calls)
  r = requests.post(f"{BASE}/search",
    json={"query": "bedroom with natural light"})
  assert r.status_code == 200
  data = r.json()
  print(f"POST /search          {r.status_code} OK - {data.get('total',0)} results")
  
  # 3. Listings (what ListingDetail calls)
  r = requests.get(f"{BASE}/listings")
  print(f"GET  /listings        {r.status_code}")
  
  # 4. Properties alias
  r = requests.get(f"{BASE}/properties/test")
  print(f"GET  /properties/id   {r.status_code} (404=expected if no data)")
  
  # 5. History GET (what getChatHistory calls)
  r = requests.get(f"{BASE}/history")
  assert r.status_code == 200
  print(f"GET  /history         {r.status_code} OK")
  
  # 6. History POST (what saveChatHistory calls)
  r = requests.post(f"{BASE}/history",
    json={
      "query": "test query",
      "results_count": 5,
      "parsed_intent": {}
    })
  assert r.status_code == 200
  print(f"POST /history         {r.status_code} OK")
  
  # 7. Status
  r = requests.get(f"{BASE}/status/test_job_123")
  assert r.status_code == 200
  print(f"GET  /status/id       {r.status_code} OK")
  
  # 8. Auth signup
  r = requests.post(f"{BASE}/auth/signup",
    json={
      "email": "test@propvision.ai",
      "password": "test1234",
      "full_name": "Test User",
      "role": "user"
    })
  print(f"POST /auth/signup     {r.status_code}")
  
  # 9. Auth login
  r = requests.post(f"{BASE}/auth/login",
    json={
      "email": "test@propvision.ai",
      "password": "test1234"
    })
  print(f"POST /auth/login      {r.status_code}")
  
  print("=" * 40)
  print("ALL ENDPOINTS TESTED")

if __name__ == "__main__":
    test_all()
