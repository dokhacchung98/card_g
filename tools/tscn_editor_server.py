#!/usr/bin/env python3
"""
Lightweight local HTTP daemon on 127.0.0.1:3457 that allows any <hero_id>_editor.html
(opened either via file:// or http://127.0.0.1:3457/) to save updated .tscn files
directly to disk and persist the updated STATE inside the HTML editor file.
"""
import os
import re
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler

WORKSPACE_ROOT = "/Users/dochung/Desktop/card_g"

class TscnEditorHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WORKSPACE_ROOT, **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        if self.path == "/save-tscn":
            length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(length).decode("utf-8")
            payload = json.loads(raw_body)
            tscn_path = payload.get("tscn_path", "")
            tscn_content = payload.get("tscn_content", "")
            state = payload.get("state")

            if not tscn_path.startswith(WORKSPACE_ROOT) or not tscn_path.endswith(".tscn"):
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": "Invalid tscn_path"}).encode("utf-8"))
                return

            os.makedirs(os.path.dirname(tscn_path), exist_ok=True)
            with open(tscn_path, "w", encoding="utf-8") as f:
                f.write(tscn_content)

            # Also persist the updated STATE into <hero_dir>/<hero_id>_editor.html and state.json
            hero_dir = os.path.dirname(os.path.dirname(tscn_path))
            if state:
                state_json_path = os.path.join(hero_dir, "godot", "rig_state.json")
                with open(state_json_path, "w", encoding="utf-8") as sf:
                    json.dump(state, sf, ensure_ascii=False, indent=2)
                for fn in os.listdir(hero_dir):
                    if fn.endswith("_editor.html"):
                        html_p = os.path.join(hero_dir, fn)
                        with open(html_p, "r", encoding="utf-8") as hf:
                            html_txt = hf.read()
                        new_state_line = "const STATE = " + json.dumps(state, ensure_ascii=False) + ";"
                        html_txt = re.sub(r"^const STATE = .*?;$", new_state_line, html_txt, count=1, flags=re.MULTILINE)
                        with open(html_p, "w", encoding="utf-8") as hf:
                            hf.write(html_txt)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True, "saved_path": tscn_path}).encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 3457), TscnEditorHandler)
    print("TSCN Editor Save Server listening on http://127.0.0.1:3457")
    server.serve_forever()

