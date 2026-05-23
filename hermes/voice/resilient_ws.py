import asyncio
import random
import websockets
from typing import AsyncIterator
from voice.elevenlabs_ws import ElevenLabsVoiceStream

class ResilientVoiceStream:
    """
    Wrapper resiliente para el cliente de voz que maneja reintentos automaticos
    y conmuta a servidores redundantes de ElevenLabs en caso de caida.
    """
    def __init__(self):
        self.primary = ElevenLabsVoiceStream()
        self.backup_region = "api.us.elevenlabs.io"
        self.max_retries = 3

    async def stream_with_fallback(self, text_stream: AsyncIterator[str]) -> AsyncIterator[bytes]:
        """
        Consume el stream de texto y produce bytes de audio de forma robusta.
        Si la conexion falla, cambia al endpoint backup de EE.UU. y reintenta.
        """
        attempt = 0
        while attempt < self.max_retries:
            try:
                # Intentamos consumir el streaming de audio
                async for audio_chunk in self.primary.stream_text(text_stream):
                    yield audio_chunk
                # Si se ejecuta sin excepciones, completamos la transicion
                return
            except (websockets.exceptions.WebSocketException, ConnectionRefusedError, asyncio.TimeoutError) as e:
                attempt += 1
                print(f"Error de conexion en ElevenLabs (Intento {attempt}/{self.max_retries}): {e}")
                
                if attempt >= self.max_retries:
                    raise e
                
                # Conmutar endpoint al servidor de respaldo
                self.primary.ENDPOINT = f"wss://{self.backup_region}/v1/text-to-speech/{{voice_id}}/stream-input"
                
                # Tiempo de espera con backoff exponencial y jitter
                wait_time = (2 ** attempt) * 0.25 + random.uniform(0.1, 0.4)
                await asyncio.sleep(wait_time)
            except Exception as e:
                # Otras excepciones fatales no reintentables de inmediato
                print(f"Error inesperado en streaming de voz: {e}")
                raise e
