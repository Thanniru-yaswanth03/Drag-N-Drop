import urllib.request, json, sys
sys.stdout.reconfigure(encoding='utf-8')
BASE = "http://127.0.0.1:8000"

# GET the board first
r = urllib.request.urlopen(f"{BASE}/api/board?username=user", timeout=5)
board = json.loads(r.read())
card_id = list(board["cards"].keys())[0]
print("Board GET: OK -", len(board["cards"]), "cards")

# Try PUT to save task details
board["cards"][card_id].update({"priority": "high", "dueDate": "2026-12-31", "tags": ["e2e"], "assignee": "user"})
data = json.dumps(board).encode()
req = urllib.request.Request(f"{BASE}/api/board?username=user", data=data, method="PUT")
req.add_header("Content-Type", "application/json")
try:
    res = urllib.request.urlopen(req, timeout=5)
    saved = json.loads(res.read())
    sc = saved["cards"][card_id]
    print(f"Board PUT: OK - priority={sc.get('priority')} due={sc.get('dueDate')} tags={sc.get('tags')}")
except Exception as e:
    print("Board PUT: ERR", e)

# Try POST instead
data2 = json.dumps(board).encode()
req2 = urllib.request.Request(f"{BASE}/api/board?username=user", data=data2, method="POST")
req2.add_header("Content-Type", "application/json")
try:
    res2 = urllib.request.urlopen(req2, timeout=5)
    print("Board POST: OK", res2.status)
except Exception as e:
    print("Board POST: ERR", e)
