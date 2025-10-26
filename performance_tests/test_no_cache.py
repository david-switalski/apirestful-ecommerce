import httpx
import time
import statistics
import redis

import os
from dotenv import load_dotenv

API_URL = "http://localhost:8000/products/4"  # The product ID must exist
NUM_REQUESTS = 100  

load_dotenv()

REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

try:
    r = redis.Redis(
        host='localhost',  
        port=6379,
        password=REDIS_PASSWORD, 
        db=0, 
        decode_responses=True 
    )
    r.ping()
    print("Connection with Redis successful")
except redis.exceptions.ConnectionError as e:
    print(f"Redis conecction error: {e}")
    exit() 
    
def measure_without_cache():
    response_times = []
    print("\nStart measurements without cache")
    for i in range(NUM_REQUESTS):

        r.flushdb()
        
        start_time = time.perf_counter()
        with httpx.Client() as client:
            response = client.get(API_URL)
            response.raise_for_status()
        end_time = time.perf_counter()
        
        response_times.append((end_time - start_time) * 1000)
        print(f"Request {i+1}/{NUM_REQUESTS}: {response_times[-1]:.2f} ms (NO CACHE)")

    return statistics.mean(response_times)

if __name__ == "__main__":
    avg_time_db = measure_without_cache()
    print("\n--- Results ---")
    print(f"Average response time (access DB): {avg_time_db:.2f} ms")