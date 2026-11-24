import os
import sys
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.stdout.reconfigure(encoding='utf-8')
import time
import json
import threading
import urllib.request
import urllib.parse

# 1. Test app.py backend imports and SpotifyBridge
import app

print("--- [VERIFY 1] Backend & SpotifyBridge Instantiation ---")
assert hasattr(app, 'spotify_bridge'), "app.spotify_bridge missing!"
assert hasattr(app, 'get_spotify_auth_file_path'), "get_spotify_auth_file_path missing!"
print("[OK] app.spotify_bridge exists.")
print("[OK] get_spotify_auth_file_path():", app.get_spotify_auth_file_path())

# 2. Test DesktopBridge wrappers
bridge = app.DesktopBridge()
status = bridge.spotify_get_status()
assert isinstance(status, dict), "spotify_get_status did not return dict"
print("[OK] bridge.spotify_get_status() succeeded:", status.get("mode"), "ClientId:", status.get("clientId"))

# Test control through DesktopBridge (should not crash or throw NameError)
ctl_res = bridge.spotify_control("get_status")
assert isinstance(ctl_res, dict), "spotify_control did not return dict"
print("[OK] bridge.spotify_control() succeeded.")

# Test config through DesktopBridge (preserve user's existing local auth Client ID!)
orig_cid = status.get("clientId", "")
cfg_res = bridge.spotify_set_config(client_id=orig_cid or "demo_spotify_client_id_for_test")
assert isinstance(cfg_res, dict), "spotify_set_config did not return dict"
if orig_cid:
    bridge.spotify_set_config(client_id=orig_cid)
print("[OK] bridge.spotify_set_config() succeeded.")

# 3. Test HTTP Server endpoints live
print("\n--- [VERIFY 2] Live HTTP Sync Server & Spotify Endpoints ---")
server = app.start_local_sync_server(app.get_asset_path("studypulse.html"), bridge, initial_port=42069)
time.sleep(0.5)

base_url = f"http://127.0.0.1:{server.server_port}"

# Test GET /
req = urllib.request.urlopen(f"{base_url}/", timeout=3)
html_data = req.read().decode("utf-8")
assert len(html_data) > 100000, "HTML served was truncated!"
print(f"[OK] GET / returned {len(html_data)} bytes.")

# Verify the 3 cards are NOT present in served HTML
assert "Synthwave Deep Code" not in html_data, "Synthwave Deep Code still in HTML!"
assert "Classical Study & Math" not in html_data, "Classical Study & Math still in HTML!"
assert "Binaural Alpha Waves" not in html_data, "Binaural Alpha Waves still in HTML!"
print("[OK] 3 residual preset cards successfully eliminated from HTML.")

# Verify Single-Task modal doesn't have initial 'flex' class
assert 'id="onething-modal" data-alias="single-task-overlay" onclick="if(event.target===this)exitSingleTaskMode();" class="fixed inset-0 bg-ink-950/60 dark:bg-black/70 backdrop-blur-md z-[9999] hidden items-center justify-center p-4"' in html_data, "onething-modal class mismatch!"
print("[OK] Single-Task modal has clean 'hidden' class without conflicting 'flex'.")

# Test GET /api/spotify/status
req = urllib.request.urlopen(f"{base_url}/api/spotify/status", timeout=3)
spot_st = json.loads(req.read().decode("utf-8"))
assert "connected" in spot_st and "clientId" in spot_st, "Invalid status response!"
print("[OK] GET /api/spotify/status returned valid schema:", spot_st.get("clientId"))

# Test POST /api/spotify/control
ctrl_payload = json.dumps({"action": "get_status"}).encode("utf-8")
post_req = urllib.request.Request(f"{base_url}/api/spotify/control", data=ctrl_payload, headers={"Content-Type": "application/json"})
req = urllib.request.urlopen(post_req, timeout=3)
post_resp = json.loads(req.read().decode("utf-8"))
assert "connected" in post_resp, "Invalid control response!"
print("[OK] POST /api/spotify/control responded cleanly.")

# Test GET /api/spotify/playlists
req = urllib.request.urlopen(f"{base_url}/api/spotify/playlists", timeout=3)
pl_resp = json.loads(req.read().decode("utf-8"))
assert "status" in pl_resp and "playlists" in pl_resp, "Invalid playlists response!"
print("[OK] GET /api/spotify/playlists responded cleanly.")

server.shutdown()
print("[SUCCESS] All backend checks passed 100%!")
