#!/usr/bin/env python3
"""
Browser Extension Support for OmniCoder-AGI CLI

Provides integration with browser extensions for code editing.
"""

from __future__ import annotations

import json
import threading
import http.server
import socketserver
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict

@dataclass
class ExtensionMessage:
    """Message from browser extension."""
    type: str
    action: str
    data: Dict[str, Any]
    timestamp: str
    
    @classmethod
    def from_json(cls, json_str: str) -> "ExtensionMessage":
        data = json.loads(json_str)
        return cls(
            type=data.get("type", "unknown"),
            action=data.get("action", "unknown"),
            data=data.get("data", {}),
            timestamp=data.get("timestamp", "")
        )
    
    def to_dict(self) -> Dict:
        return asdict(self)

class ExtensionHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler for browser extension communication."""
    
    callback: Optional[Callable] = None
    
    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def do_POST(self):
        """Handle POST requests from extension."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        
        try:
            message = ExtensionMessage.from_json(body)
            
            # Process message
            response = self._process_message(message)
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    
    def do_GET(self):
        """Handle GET requests (health check)."""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "running",
            "name": "OmniCoder-AGI Extension Server"
        }).encode())
    
    def _process_message(self, message: ExtensionMessage) -> Dict:
        """Process a message from the extension."""
        
        if ExtensionHandler.callback:
            return ExtensionHandler.callback(message)
        
        # Default handlers
        if message.action == "analyze":
            return {
                "success": True,
                "message": "Code analysis complete",
                "data": {"issues": [], "suggestions": []}
            }
        elif message.action == "fix":
            return {
                "success": True,
                "message": "Fix applied",
                "data": {"fixed": True}
            }
        elif message.action == "generate":
            return {
                "success": True,
                "message": "Code generated",
                "data": {"code": "// Generated code"}
            }
        else:
            return {
                "success": True,
                "message": f"Action {message.action} received",
                "data": {}
            }
    
    def log_message(self, format, *args):
        """Suppress logging."""
        pass

class BrowserExtensionServer:
    """Server for browser extension communication."""
    
    def __init__(self, port: int = 52718):
        self.port = port
        self.server: Optional[socketserver.TCPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
    
    def start(self, callback: Optional[Callable] = None):
        """Start the extension server."""
        if self._running:
            return
        
        ExtensionHandler.callback = callback
        
        self.server = socketserver.TCPServer(("localhost", self.port), ExtensionHandler)
        self._running = True
        
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()
        
        print(f"🌐 Browser extension server running on http://localhost:{self.port}")
    
    def stop(self):
        """Stop the extension server."""
        self._running = False
        if self.server:
            self.server.shutdown()
            self.server = None
        print("🌐 Browser extension server stopped")
    
    def _serve(self):
        """Serve requests."""
        while self._running and self.server:
            self.server.handle_request()
    
    def is_running(self) -> bool:
        return self._running

# Chrome extension manifest
CHROME_EXTENSION_MANIFEST = {
    "manifest_version": 3,
    "name": "OmniCoder-AGI",
    "version": "1.0.0",
    "description": "Browser extension for OmniCoder-AGI coding assistant",
    "permissions": ["activeTab", "storage"],
    "host_permissions": ["http://localhost:52718/*"],
    "action": {
        "default_popup": "popup.html",
        "default_icon": {
            "16": "icons/icon16.png",
            "48": "icons/icon48.png",
            "128": "icons/icon128.png"
        }
    },
    "content_scripts": [{
        "matches": ["https://github.com/*", "https://*.github.io/*"],
        "js": ["content.js"]
    }],
    "background": {
        "service_worker": "background.js"
    }
}

POPUP_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>OmniCoder-AGI</title>
    <style>
        body {
            width: 300px;
            padding: 10px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        h1 { font-size: 16px; color: #333; }
        .status { padding: 10px; background: #f0f0f0; border-radius: 4px; margin: 10px 0; }
        .status.connected { background: #d4edda; color: #155724; }
        .status.disconnected { background: #f8d7da; color: #721c24; }
        button {
            width: 100%;
            padding: 10px;
            margin: 5px 0;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        .primary { background: #007bff; color: white; }
        .primary:hover { background: #0056b3; }
        .secondary { background: #6c757d; color: white; }
        .secondary:hover { background: #545b62; }
    </style>
</head>
<body>
    <h1>🤖 OmniCoder-AGI</h1>
    <div id="status" class="status disconnected">Checking connection...</div>
    <button class="primary" id="analyze">Analyze Code</button>
    <button class="primary" id="fix">Fix Issues</button>
    <button class="secondary" id="generate">Generate Code</button>
    <button class="secondary" id="settings">Settings</button>
    <script src="popup.js"></script>
</body>
</html>
"""

POPUP_JS = """
const API_URL = 'http://localhost:52718';

async function checkConnection() {
    const status = document.getElementById('status');
    try {
        const response = await fetch(API_URL);
        const data = await response.json();
        status.textContent = 'Connected to OmniCoder-AGI';
        status.className = 'status connected';
    } catch (e) {
        status.textContent = 'Not connected. Start CLI with --extension flag.';
        status.className = 'status disconnected';
    }
}

async function sendAction(action) {
    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                type: 'action',
                action: action,
                data: {},
                timestamp: new Date().toISOString()
            })
        });
        const result = await response.json();
        console.log(result);
        alert(result.message);
    } catch (e) {
        alert('Error: ' + e.message);
    }
}

document.getElementById('analyze').addEventListener('click', () => sendAction('analyze'));
document.getElementById('fix').addEventListener('click', () => sendAction('fix'));
document.getElementById('generate').addEventListener('click', () => sendAction('generate'));
document.getElementById('settings').addEventListener('click', () => {
    chrome.runtime.openOptionsPage();
});

checkConnection();
"""

BACKGROUND_JS = """
chrome.runtime.onInstalled.addListener(() => {
    console.log('OmniCoder-AGI extension installed');
});

chrome.action.onClicked.addListener((tab) => {
    chrome.action.openPopup();
});
"""

CONTENT_JS = """
// OmniCoder-AGI Content Script
console.log('OmniCoder-AGI content script loaded');

// Add context menu on right-click
document.addEventListener('contextmenu', (e) => {
    if (e.target.matches('pre, code, .blob-code, .CodeMirror')) {
        // Could add custom context menu here
    }
});
"""

def generate_extension_files(output_dir: Path):
    """Generate browser extension files."""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write manifest
    (output_dir / "manifest.json").write_text(json.dumps(CHROME_EXTENSION_MANIFEST, indent=2))
    
    # Write HTML
    (output_dir / "popup.html").write_text(POPUP_HTML)
    
    # Write JS files
    (output_dir / "popup.js").write_text(POPUP_JS)
    (output_dir / "background.js").write_text(BACKGROUND_JS)
    (output_dir / "content.js").write_text(CONTENT_JS)
    
    # Create icons directory
    icons_dir = output_dir / "icons"
    icons_dir.mkdir(exist_ok=True)
    
    print(f"✅ Extension files generated in {output_dir}")
    print("   To install in Chrome:")
    print("   1. Go to chrome://extensions/")
    print("   2. Enable Developer mode")
    print("   3. Click 'Load unpacked'")
    print(f"   4. Select {output_dir}")


def add_extension_commands(subparsers):
    """Add extension commands to CLI."""
    ext_parser = subparsers.add_parser("extension", help="Browser extension commands")
    ext_subparsers = ext_parser.add_subparsers(dest="ext_action")
    
    # Generate extension
    gen_parser = ext_subparsers.add_parser("generate", help="Generate extension files")
    gen_parser.add_argument("--output", "-o", type=Path, default=Path("browser_extension"))
    
    # Start server
    server_parser = ext_subparsers.add_parser("server", help="Start extension server")
    server_parser.add_argument("--port", type=int, default=52718)
    
    return ext_parser


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "generate":
        output = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("browser_extension")
        generate_extension_files(output)
    else:
        # Start server
        server = BrowserExtensionServer()
        server.start()
        
        try:
            input("Press Enter to stop server...")
        except KeyboardInterrupt:
            pass
        
        server.stop()
