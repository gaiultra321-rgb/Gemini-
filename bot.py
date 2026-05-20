import os
import json
import asyncio
import websockets
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

app = FastAPI()

API_KEY = os.environ.get("G")
MODEL = "models/gemini-2.5-flash"
HOST = "generativelanguage.googleapis.com"

@app.get("/")
async def serve_frontend():
    return FileResponse("index.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Browser connected via WebSocket")
    
    if not API_KEY:
        await websocket.send_text(json.dumps({"error": "API Key 'G' is missing on Render."}))
        await websocket.close()
        return

    gemini_uri = f"wss://{HOST}/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key={API_KEY}"

    try:
        async with websockets.connect(gemini_uri) as gemini_ws:
            print("Connected to Gemini API")
            
            # ১. মডেল সেটআপ মেসেজ পাঠানো
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
            
            # প্রথম রেসপন্স (সেটআপ কনফার্মেশন) রিসিভ করে নেওয়া যাতে লুপে ঝামেলা না হয়
            await gemini_ws.recv()

            # ২. ব্রাউজার থেকে অডিও নিয়ে Gemini-তে পাঠানোর টাস্ক
            async def client_to_gemini():
                try:
                    while True:
                        # ব্রাউজার থেকে ডেটা রিসিভ করা
                        data = await websocket.receive_text()
                        # সরাসরি জেমিনিকে ফরোয়ার্ড করা
                        await gemini_ws.send(data)
                except WebSocketDisconnect:
                    print("Browser disconnected")
                except Exception as e:
                    print(f"Error in client_to_gemini: {e}")

            # ৩. Gemini থেকে অ디오 এনে ব্রাউজারে পাঠানোর টাস্ক
            async def gemini_to_client():
                try:
                    async for message in gemini_ws:
                        # জেমিনির রেসপন্স ব্রাউজারে পাঠানো
                        await websocket.send_text(message)
                except Exception as e:
                    print(f"Error in gemini_to_client: {e}")

            # দুটি টাস্ক একসাথে প্যারালালি চালানো এবং যেকোনো একটি বন্ধ হলে অন্যটি হ্যান্ডেল করা
            await asyncio.gather(
                client_to_gemini(),
                gemini_to_client(),
                return_exceptions=True
            )
            
    except Exception as e:
        print(f"Gemini Connection Error: {e}")
        try:
            await websocket.send_text(json.dumps({"error": f"Gemini Connection Failed: {str(e)}"}))
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass
        print("WebSocket Endpoint Closed")
            
