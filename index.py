from http.server import BaseHTTPRequestHandler
import json
import urllib.parse

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Configurar headers con CORS
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
            self.end_headers()
            
            # Parse URL path
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path
            
            # Routing simple
            if path == '/' or path == '/api':
                response = {
                    "status": "working", 
                    "message": "API funcionando en Vercel - Version 7 con CORS",
                    "endpoints": ["/", "/health", "/api/test"],
                    "frontend_ready": True
                }
            elif path == '/health':
                response = {"status": "ok", "service": "tickets-api", "version": "7"}
            elif path == '/api/test' or path == '/test':
                response = {"test": "success", "platform": "vercel", "version": "7", "cors_enabled": True}
            else:
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                response = {"error": "Not found", "path": path, "available": ["/", "/health", "/api/test"]}
            
            # Send response
            self.wfile.write(json.dumps(response, indent=2).encode('utf-8'))
            
        except Exception as e:
            # Error handling
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_response = {"error": "Internal server error", "details": str(e)}
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
        
    def do_POST(self):
        self.do_GET()  # Handle POST same as GET for now
        
    def do_PUT(self):
        self.do_GET()  # Handle PUT same as GET for now
        
    def do_DELETE(self):
        self.do_GET()  # Handle DELETE same as GET for now
        
    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()