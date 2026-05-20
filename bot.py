import os
import json
import asyncio
import websockets
from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse

app = FastAPI()

# Render এর এনভায়রনমেন্ট ভেরিয়েবল থেকে API Key নেওয়া হচ্ছে
API_KEY = os.environ.get("G")
MODEL = "models/gemini-2.5-flash"
HOST = "generativelanguage.googleapis.com"

# ফ্রন্টএন্ড পেজ সার্ভ করা
@app.get("/")
async def serve_frontend():
    return FileResponse("index.html")

# ব্রাউজারের সাথে WebSocket কানেকশন
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    if not API_KEY:
        await websocket.send_text(json.dumps({"error": "API Key 'G' is missing on server."}))
        await websocket.close()
        return

    gemini_uri = f"wss://{HOST}/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key={API_KEY}"

    try:
        # Gemini-এর সাথে কানেক্ট করা
        async with websockets.connect(gemini_uri) as gemini_ws:
            
            # ১. মডেল সেটআপ
            setup_msg = {
                "setup": {
                    "model": MODEL,
                    "generationConfig": {
                        "responseModalities": ["AUDIO"],
                        "speechConfig": {
                            "voiceConfig": {
                                "prebuiltVoiceConfig": {"voiceName": "Aoede"}
                            }
                        }
                    }
                }
            }
            await gemini_ws.send(json.dumps(setup_msg))
            await gemini_ws.recv() # সেটআপ কনফার্মেশন

            # ২. ব্রাউজার থেকে অডিও নিয়ে Gemini কে পাঠানো
            async def client_to_gemini():
                try:
                    while True:
                        data = await websocket.receive_text()
                        await gemini_ws.send(data)
                except Exception:
                    pass

            # ৩. Gemini থেকে অডিও এনে ব্রাউজারে পাঠানো
            async def gemini_to_client():
                try:
                    async for message in gemini_ws:
                        await websocket.send_text(message)
                except Exception:
                    pass

            # দুটি কাজ একসাথে চালানো
            await asyncio.gather(client_to_gemini(), gemini_to_client())
            
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        await websocket.close()
                                  
