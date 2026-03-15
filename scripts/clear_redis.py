import redis
import os
from dotenv import load_dotenv

load_dotenv()

def clear_redis():
    try:
        r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
        keys = r.keys("anon_search_count:*")
        if keys:
            r.delete(*keys)
            print(f"Cleared {len(keys)} rate limit keys from Redis.")
        else:
            print("No rate limit keys found in Redis.")
    except Exception as e:
        print(f"Error clearing Redis: {e}")

if __name__ == "__main__":
    clear_redis()
