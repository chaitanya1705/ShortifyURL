
import requests
import threading
import time

URL = "http://<URL>/shorten"
NUM_THREADS = 50
DURATION = 30  # in seconds

success_count = 0
failure_count = 0
log = []
lock = threading.Lock()

def attack():
    global success_count, failure_count
    payload = {"url": "https://example.com"}
    while time.time() < end:
        try:
            with lock:
                log.append("🔌 Connecting to server...")
            start = time.time()
            r = requests.post(URL, json=payload)
            elapsed = round(time.time() - start, 3)
            with lock:
                if r.status_code == 200:
                    success_count += 1
                    instance_id = r.json().get('instance_id', 'N/A')
                    log.append(f"✅ 200 OK from {instance_id} - {elapsed}s")
                else:
                    failure_count += 1
                    log.append(f"❌ {r.status_code} - {elapsed}s")
        except Exception as e:
            with lock:
                failure_count += 1
                log.append(f"❌ Error: {str(e)}")

end = time.time() + DURATION
threads = [threading.Thread(target=attack) for _ in range(NUM_THREADS)]
[t.start() for t in threads]
[t.join() for t in threads]

total_requests = success_count + failure_count
success_rate = (success_count / total_requests) * 100 if total_requests else 0
failure_rate = (failure_count / total_requests) * 100 if total_requests else 0

print("\n=== Request Logs ===")
for entry in log:
    print(entry)

print("\n=== Stress Test Summary ===")
print(f"Total Requests: {total_requests}")
print(f"Successful Requests: {success_count}")
print(f"Failed Requests: {failure_count}")
print(f"Success Rate: {success_rate:.2f}%")
print(f"Failure Rate: {failure_rate:.2f}%")
