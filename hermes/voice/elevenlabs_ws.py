import os
import json
import asyncio
import websockets
import base64
from typing import AsyncIterator


class ElevenLabsVoiceStream:
    """
    Cliente WebSocket para ElevenLabs Flash v2.5
    con streaming bidireccional de baja latencia.
    """

    ENDPOINT = "wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input"

    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY", "")
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
        self.ws = None

    async def connect(self):
        """Establece conexion WebSocket con configuracion optimizada."""
        if not self.api_key:
            raise ValueError("Falta la variable de entorno ELEVENLABS_API_KEY.")

        uri = self.ENDPOINT.format(voice_id=self.voice_id)

        # Desactivamos compresion y pings automatizados para mejorar la latencia
        self.ws = await websockets.connect(
            uri,
            extra_headers={"xi-api-key": self.api_key},
            compression=None,
            ping_interval=None,
        )

        # Enviar configuracion inicial (auto_mode para deshabilitar buffers manuales)
        init_payload = {
            "text": " ",  # Espacio para inicializar
            "model_id": "eleven_flash_v2_5",
            "language_code": "es",
            "voice_settings": {
                "stability": 0.50,
                "similarity_boost": 0.70,
                "use_speaker_boost": True,
            },
            "auto_mode": True,
            "output_format": "pcm_24000",
        }
        await self.ws.send(json.dumps(init_payload))

    async def stream_text(
        self, text_stream: AsyncIterator[str]
    ) -> AsyncIterator[bytes]:
        """Envia texto por partes y produce los bytes de audio recibidos."""
        if not self.ws:
            await self.connect()

        async def send_text_chunks():
            try:
                async for text in text_stream:
                    if text and self.ws:
                        # Enviar trozo de texto a procesar
                        await self.ws.send(
                            json.dumps({"text": text, "try_trigger_generation": True})
                        )
                # Mensaje de finalizacion requerido por ElevenLabs
                if self.ws:
                    await self.ws.send(json.dumps({"text": ""}))
            except Exception as e:
                print(f"Error enviando chunks a ElevenLabs: {e}")

        # Ejecutamos el loop de envio en segundo plano
        send_task = asyncio.create_task(send_text_chunks())

        try:
            while self.ws:
                message = await self.ws.recv()
                data = json.loads(message)

                audio_b64 = data.get("audio")
                if audio_b64:
                    yield base64.b64decode(audio_b64)

                if data.get("isFinal", False):
                    break
        except websockets.exceptions.ConnectionClosed:
            print("Conexion cerrada por ElevenLabs.")
        finally:
            self.ws = None
            # Asegurar la finalizacion de la tarea de envio
            await send_task

    async def close(self):
        """Cierra el socket si estuviera activo."""
        if self.ws:
            try:
                await self.ws.close()
            except Exception:
                pass
            self.ws = None
