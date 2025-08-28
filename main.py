from fastapi import FastAPI, Response
from pydantic import BaseModel, Field
from typing import List, Optional
import uvicorn
import logging
import os
import httpx
from dotenv import load_dotenv
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer
from gtts import gTTS
import asyncio

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WhatsApp API configuration
WHATSAPP_API_TOKEN = os.getenv("WHATSAPP_API_TOKEN")
GRAPH_API_VERSION = "v19.0"
BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"
RESPONSE_TEXT = "Thanks for calling us. Have a nice day!"
AUDIO_FILE = "response.mp3"

# Pydantic models for WhatsApp webhook
class CallSession(BaseModel):
    sdp_type: str
    sdp: str

class Call(BaseModel):
    id: str
    to: str
    from_: str = Field(..., alias='from')
    event: str
    timestamp: str
    session: Optional[CallSession] = None
    direction: Optional[str] = None
    status: Optional[list[str]] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration: Optional[int] = None

class Metadata(BaseModel):
    phone_number_id: str
    display_phone_number: str

class Value(BaseModel):
    messaging_product: str
    metadata: Metadata
    calls: List[Call]

class Change(BaseModel):
    value: Value
    field: str

class Entry(BaseModel):
    id: str
    changes: List[Change]

class WhatsAppWebhook(BaseModel):
    object: str
    entry: List[Entry]

app = FastAPI()

# In-memory store for peer connections
pcs = {}

@app.on_event("startup")
async def startup_event():
    if not os.path.exists(AUDIO_FILE):
        logger.info(f"Generating audio file for text: '{RESPONSE_TEXT}'")
        tts = gTTS(text=RESPONSE_TEXT, lang='en')
        tts.save(AUDIO_FILE)
        logger.info(f"Audio file saved as {AUDIO_FILE}")

async def send_whatsapp_api_request(phone_number_id: str, payload: dict):
    url = f"{BASE_URL}/{phone_number_id}/calls"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_API_TOKEN}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Error sending WhatsApp API request: {e.response.text}")
            raise

async def terminate_call(phone_number_id: str, call_id: str):
    logger.info(f"Terminating call (call_id: {call_id})")
    payload = {
        "messaging_product": "whatsapp",
        "call_id": call_id,
        "action": "terminate",
    }
    await send_whatsapp_api_request(phone_number_id, payload)
    logger.info(f"Call terminated request sent for call_id: {call_id}")


@app.post("/whatsapp/webhook")
async def whatsapp_webhook(webhook_data: WhatsAppWebhook):
    logger.info(f"Received webhook: {webhook_data.model_dump_json(indent=2)}")

    for entry in webhook_data.entry:
        for change in entry.changes:
            if change.field == "calls":
                phone_number_id = change.value.metadata.phone_number_id
                for call in change.value.calls:
                    if call.event == "connect" and call.session:
                        logger.info(f"Incoming call (call_id: {call.id})")

                        pc = RTCPeerConnection()
                        pcs[call.id] = pc
                        player = MediaPlayer(AUDIO_FILE)

                        @pc.on("connectionstatechange")
                        async def on_connectionstatechange():
                            logger.info(f"Connection state is {pc.connectionState}")
                            if pc.connectionState == "failed":
                                await pc.close()
                                pcs.pop(call.id, None)

                        @player.audio.on("ended")
                        async def on_ended():
                            logger.info("Audio playback finished")
                            await terminate_call(phone_number_id, call.id)

                        offer = RTCSessionDescription(sdp=call.session.sdp, type=call.session.sdp_type)
                        await pc.setRemoteDescription(offer)

                        pc.addTrack(player.audio)

                        answer = await pc.createAnswer()
                        await pc.setLocalDescription(answer)

                        logger.info(f"SDP Answer created for call_id: {call.id}")

                        # Pre-accept the call
                        pre_accept_payload = {
                            "messaging_product": "whatsapp",
                            "call_id": call.id,
                            "action": "pre_accept",
                            "session": {
                                "sdp_type": "answer",
                                "sdp": pc.localDescription.sdp,
                            },
                        }
                        await send_whatsapp_api_request(phone_number_id, pre_accept_payload)
                        logger.info(f"Pre-accepted call (call_id: {call.id})")

                        # Accept the call
                        accept_payload = {
                            "messaging_product": "whatsapp",
                            "call_id": call.id,
                            "action": "accept",
                            "session": {
                                "sdp_type": "answer",
                                "sdp": pc.localDescription.sdp,
                            },
                        }
                        await send_whatsapp_api_request(phone_number_id, accept_payload)
                        logger.info(f"Accepted call (call_id: {call.id})")

                    elif call.event == "terminate":
                        logger.info(f"Call terminated (call_id: {call.id})")
                        pc = pcs.pop(call.id, None)
                        if pc:
                            await pc.close()

    return Response(status_code=200)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
