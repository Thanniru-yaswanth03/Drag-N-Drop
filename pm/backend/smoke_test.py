import urllib.request, json, sys

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

BASE = "http://127.0.0.1:8000"

def req(label, url, method="GET", body=None):
    try:
        data = json.dumps(body).encode() if body else None
        r = urllib.request.Request(url, data=data, method=method)
        r.add_header("Content-Type", "application/json")
        res = urllib.request.urlopen(r, timeout=5)
        ct = res.headers["content-type"]
        raw = res.read()
        is_json = "application/json" in ct
        try:
            parsed = json.loads(raw)
            summary = json.dumps(parsed)[:80]
        except:
            summary = raw[:80].decode(errors="replace")
        status = "PASS" if is_json else "FAIL(HTML)"
        print(f"{status} [{label}] {res.status} | {summary}")
        return parsed if is_json else None
    except Exception as e:
        print(f"ERR  [{label}] {e}")
        return None

print("\n=== PART 1-3: Auth & Board ===")
req("Health",      f"{BASE}/api/health")
req("Login",       f"{BASE}/api/auth/login",  "POST", {"username":"user","password":"password"})
board = req("Board GET",   f"{BASE}/api/board?username=user")
if board:
    print(f"   columns={len(board['columns'])} cards={len(board['cards'])}")

print("\n=== PART 11: Task Details (Priority, Tags, Due Date, Assignee) ===")
if board:
    card_id = list(board['cards'].keys())[0]
    card = board["cards"][card_id]
    updated_board = {**board, "cards": {**board["cards"], card_id: {
        **card,
        "priority": "high",
        "dueDate": "2026-12-31",
        "tags": ["e2e", "verified"],
        "assignee": "testuser",
        "description": "E2E verification description"
    }}}
    saved = req("Save Task Details", f"{BASE}/api/board?username=user", "POST", updated_board)
    if saved:
        sc = saved["cards"].get(card_id, {})
        print(f"   priority={sc.get('priority')} due={sc.get('dueDate')} tags={sc.get('tags')} assignee={sc.get('assignee')}")

print("\n=== PART 12: Filter/Sort data check ===")
board2 = req("Board re-fetch", f"{BASE}/api/board?username=user")
if board2:
    cards = list(board2["cards"].values())
    print(f"   Total cards: {len(cards)}")
    print(f"   Cards with priority: {sum(1 for c in cards if c.get('priority'))}")
    print(f"   Cards with tags: {sum(1 for c in cards if c.get('tags'))}")

print("\n=== PART 13: Multiple Projects ===")
projects = req("Projects LIST",  f"{BASE}/api/projects?username=user")
if projects:
    print(f"   {len(projects)} project(s): {[p['name'] for p in projects]}")

new_proj = req("Project CREATE", f"{BASE}/api/projects?username=user", "POST", {"name": "Verification Project"})
if new_proj:
    print(f"   Created: {new_proj['name']} id={new_proj['id']}")
    proj_board = req("New Project Board", f"{BASE}/api/board?username=user&project_id={new_proj['id']}")
    if proj_board:
        print(f"   Empty board: {len(proj_board['columns'])} cols, {len(proj_board['cards'])} cards")
    renamed = req("Project RENAME", f"{BASE}/api/projects/{new_proj['id']}?username=user", "PUT", {"name": "Renamed Project"})
    if renamed:
        print(f"   Renamed to: {renamed['name']}")
    deleted = req("Project DELETE", f"{BASE}/api/projects/{new_proj['id']}?username=user", "DELETE")
    print(f"   Deleted: {deleted}")

print("\n=== AI Integration ===")
req("AI connection test", f"{BASE}/api/ai/test", "POST")

print("\n=== Frontend Static Files ===")
r = urllib.request.urlopen(f"{BASE}/", timeout=5)
body = r.read()
is_html = b"<html" in body or b"<!DOCTYPE" in body
has_next = b"_next" in body
print(f"{'PASS' if is_html and has_next else 'FAIL'} [Frontend] HTML={is_html} Next.js={has_next} size={len(body)}b")

print(f"\nApp is live at: {BASE}")
