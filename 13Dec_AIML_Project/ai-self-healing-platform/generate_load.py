import requests, time, sys
from datetime import datetime

url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:40182"
duration = int(sys.argv[2]) if len(sys.argv) > 2 else 60
rate = int(sys.argv[3]) if len(sys.argv) > 3 else 10

print(f"Load Generator\nTarget: {url}\nDuration: {duration}s\nRate: {rate} req/s\n")

try:
    r = requests.get(f"{url}/health", timeout=5)
    print(f"✅ Connected: {r.json()}\n")
except:
    print(f"❌ Cannot connect to {url}")
    sys.exit(1)

start = time.time()
count = 0
success = 0

while (time.time() - start) < duration:
    try:
        r = requests.get(f"{url}/compute", timeout=10)
        if r.status_code == 200:
            success += 1
        count += 1
        if count % 10 == 0:
            print(f"[{int(time.time()-start)}s] Sent: {count} | Success: {success}")
        time.sleep(1.0/rate)
    except KeyboardInterrupt:
        break
    except:
        count += 1

print(f"\n✅ Complete: {count} requests | {success} successful ({success/count*100:.1f}%)")