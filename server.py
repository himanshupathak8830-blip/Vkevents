import http.server
import socketserver
import json
import os
import base64
import urllib.parse
import fcntl
from datetime import datetime

PORT = 8000
DIRECTORY = os.path.abspath(os.path.dirname(__file__))

# Data files paths
ENQUIRIES_FILE = os.path.join(DIRECTORY, "enquiries.json")
IMAGES_METADATA_FILE = os.path.join(DIRECTORY, "images.json")
IMAGES_DIR = os.path.join(DIRECTORY, "images")

# Ensure images directory exists
if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)

# --- Helper Functions for Data Handling ---

def read_json_file(file_path, default_value=None):
    """Safely reads and decodes a JSON file."""
    if not os.path.exists(file_path):
        return default_value
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_SH) # Shared lock for reading
            data = json.load(f)
            fcntl.flock(f, fcntl.LOCK_UN)
            return data
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading {file_path}: {e}")
        return default_value

def write_json_file(file_path, data):
    """Safely writes data to a JSON file."""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX) # Exclusive lock for writing
            json.dump(data, f, indent=2, ensure_ascii=False)
            fcntl.flock(f, fcntl.LOCK_UN)
    except IOError as e:
        print(f"Error writing to {file_path}: {e}")
        raise

class LocalDatabaseHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        # 1. API: Get enquiries
        if path == "/api/enquiries":
            self.send_json_response(self.get_enquiries())
            return
            
        # 2. API: Get images mapping
        elif path == "/api/images":
            self.send_json_response(self.get_images())
            return

        # 3. Handle default root route mapping to main organizer file
        elif path == "/" or path == "/index.html":
            self.path = "/vk-event-organizer (2).html"

        super().do_GET()

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        # Read POST body length and parse JSON
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
        except Exception as e:
            self.send_json_response({"success": False, "error": "Invalid JSON: " + str(e)}, status=400)
            return

        # 1. API: Save enquiry
        if path == "/api/enquiries":
            result = self.save_enquiry(data)
            self.send_json_response(result)
            
        # 2. API: Save uploaded image
        elif path == "/api/upload":
            result = self.save_image(data)
            self.send_json_response(result)
            
        else:
            self.send_json_response({"success": False, "error": "Not Found"}, status=404)

    # Helper: Send JSON response
    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    # Database: Get enquiries
    def get_enquiries(self):
        enquiries = read_json_file(ENQUIRIES_FILE, default_value=[])
        if enquiries is not None:
            return {"success": True, "enquiries": enquiries}
        else:
            return {"success": False, "error": "Could not read enquiries data.", "enquiries": []}

    # Database: Save enquiry
    def save_enquiry(self, data):
        enquiries = read_json_file(ENQUIRIES_FILE, default_value=[])
        if enquiries is None:
            return {"success": False, "error": "Failed to read existing enquiries before saving."}
                
        # Build enquiry object
        new_enquiry = {
            "timestamp": datetime.now().isoformat(),
            "name": data.get("name", ""),
            "phone": data.get("phone", ""),
            "email": data.get("email", ""),
            "eventType": data.get("eventType", ""),
            "eventDate": data.get("eventDate", ""),
            "guests": data.get("guests", ""),
            "requirements": data.get("requirements", ""),
        }
        
        # Add to top (newest first)
        enquiries.insert(0, new_enquiry)
        
        try:
            write_json_file(ENQUIRIES_FILE, enquiries)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Database: Get images mapping
    def get_images(self):
        images = read_json_file(IMAGES_METADATA_FILE, default_value={})
        if images is None:
            images = {} # Recover from read error by starting fresh
        # Check standard slots for local overrides
        slots = [
            'aboutImg', 'svc1img', 'svc2img', 'svc3img', 'svc4img', 'svc5img', 'svc6img', 'svc7img', 'svc8img',
            'hosp1img', 'hosp2img', 'hosp3img',
            'g1img', 'g2img', 'g3img', 'g4img', 'g5img'
        ]
        for slot in slots:
            if slot not in images:
                local_path = os.path.join(IMAGES_DIR, f"{slot}.jpg")
                if os.path.exists(local_path):
                    images[slot] = f"images/{slot}.jpg"
                    
        return {"success": True, "images": images}

    # Database: Save uploaded image
    def save_image(self, data):
        slot_id = data.get("slotId")
        base64_data = data.get("base64Data")
        
        if not slot_id or not base64_data:
            return {"success": False, "error": "Missing slotId or base64Data"}

        # Security: Sanitize slot_id to prevent path traversal
        if ".." in slot_id or "/" in slot_id or "\\" in slot_id:
            return {"success": False, "error": "Invalid slotId"}
            
        try:
            # Decode base64
            img_bytes = base64.b64decode(base64_data)
            
            # Save file locally
            filename = f"{slot_id}.jpg"
            with open(os.path.join(IMAGES_DIR, filename), "wb") as f:
                f.write(img_bytes)
                
            # Update metadata
            images = read_json_file(IMAGES_METADATA_FILE, default_value={})
            if images is None:
                return {"success": False, "error": "Failed to read image metadata before saving."}
            
            relative_url = f"images/{filename}"
            images[slot_id] = relative_url
            
            write_json_file(IMAGES_METADATA_FILE, images)
                
            return {"success": True, "imageUrl": relative_url}
            
        except base64.binascii.Error as e:
            return {"success": False, "error": f"Invalid base64 data: {e}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

# Running the server
socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), LocalDatabaseHandler) as httpd:
    print(f"Local VK database server running on port {PORT}...")
    print(f"Main site: http://localhost:{PORT}/")
    print(f"Admin panel: http://localhost:{PORT}/admin.html")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
