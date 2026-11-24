import re

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace DesktopBridge.__init__
old_init = """    def __init__(self):
        self._window = None
        self._is_maximized = False
        self._restore_bounds = None"""

new_init = """    def __init__(self):
        self._window = None
        self._is_maximized = False
        self._restore_bounds = None
        self._slice_lock = _ai_inference_lock"""

if old_init in content:
    content = content.replace(old_init, new_init, 1)
    print("DesktopBridge.__init__ updated!")
else:
    print("Warning: old_init not found!")

# Replace /api/ai/slice
old_slice = """        elif parsed.path == "/api/ai/slice":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8")
                req_data = json.loads(body)
                prompt = req_data.get("prompt", "")
                engine = req_data.get("engine", "neural")
                if engine == "smart":
                    result = smart_multidomain_slice(prompt)
                else:
                    result = run_ephemeral_llama_slice(prompt)"""

new_slice = """        elif parsed.path == "/api/ai/slice":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8")
                req_data = json.loads(body)
                prompt = req_data.get("prompt", "")
                engine = req_data.get("engine", "neural")
                with _ai_inference_lock:
                    if engine == "smart":
                        result = smart_multidomain_slice(prompt)
                    else:
                        result = run_ephemeral_llama_slice(prompt)"""

if old_slice in content:
    content = content.replace(old_slice, new_slice, 1)
    print("/api/ai/slice updated!")
else:
    print("Warning: old_slice not found!")

with open("app.py", "w", encoding="utf-8", newline="") as f:
    f.write(content)

print("Finished writing app.py")
