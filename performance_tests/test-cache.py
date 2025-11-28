import statistics
import time

import httpx

API_URL = "http://localhost:8000/products/4"  # The product ID must exist
NUM_REQUESTS = 100


def measure_with_cache():
    response_times = []
    with httpx.Client() as client:
        print("Making warm-up request to refill cache")
        client.get(API_URL)
        time.sleep(0.1)

        for i in range(NUM_REQUESTS):
            start_time = time.perf_counter()
            response = client.get(API_URL)
            response.raise_for_status()
            end_time = time.perf_counter()

            response_times.append(
                (end_time - start_time) * 1000
            )  # Convert to milliseconds
            print(
                f"Request {i+1}/{NUM_REQUESTS}: {response_times[-1]:.2f} ms (WITH CACHE)"
            )

    return statistics.mean(response_times)


if __name__ == "__main__":
    print("--- Start measurements with cache ---")
    avg_time_cache = measure_with_cache()
    print("\n--- Results ---")
    print(f"Average response time (access Cache): {avg_time_cache:.2f} ms")
