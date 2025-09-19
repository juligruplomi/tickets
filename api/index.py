from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Configurar CORS
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # Routing simple
        if self.path == '/':
            response = {"status": "working", "message": "API funcionando en Vercel - Version 4"}
        elif self.path == '/health':
            response = {"status": "ok", "service": "tickets-api"}
        elif self.path == '/api/test':
            response = {"test": "success", "platform": "vercel", "version": "4"}
        else:
            response = {"error": "Not found", "path": self.path}
        
        self.wfile.write(json.dumps(response).encode('utf-8'))
        
    def do_POST(self):
        self.do_GET()  # Handle POST same as GET for now