import os
import asyncio
import orjson
import aiohttp
import hashlib
from cachetools import TTLCache
from collections import deque
from typing import Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
import time
import re


class HermesAgent:
    """
    Agente autonomo con capacidad de auto-modificacion controlada.
    Directiva Zero-PR: Los cambios se integran automaticamente
    sin requerir aprobacion manual.
    """

    def __init__(self):
        self.litellm_url = os.getenv("LITELLM_URL", "http://litellm:4000")
        self.litellm_key = os.getenv("LITELLM_KEY", "")
        self.model = os.getenv(
            "HERMES_MODEL", "gemini-flash"
        )  # gemini-flash: más rápido y barato via LiteLLM
        self.max_tokens = 200  # Restriccion estricta
        self.temperature = 0.35  # Determinismo prioritario

        # Directorios auto-gestionados
        self.skills_dir = "/app/skills"
        self.data_dir = "/app/data"
        self.logs_dir = "/app/logs"

        # Estado interno — deque acota memoria sin romper slicing [-4:]
        self.conversation_history: deque = deque(maxlen=20)
        self.execution_log: list = []

        # Sesion HTTP compartida — se inicializa en start()
        self._session: aiohttp.ClientSession | None = None

        # Cache de dedup: evita llamadas API duplicadas — 300s cubre repeticiones de voz entre minutos
        self._query_cache: TTLCache = TTLCache(maxsize=256, ttl=300)

        # System Prompt v2.0 (Optimizado para Flash v2.5)
        self.system_prompt = (
            "ERES HERMES, un agente autonomo avanzado de gestion operativa.\n"
            "Tu idioma estricto y unico es el ESPANOL.\n"
            "REGLAS OPERATIVAS DE EFICIENCIA (OBLIGATORIAS):\n"
            "1. EXTREMA CONCISION: Responde de forma telegrafica, conversacional y directa. "
            "Maximo 25 palabras por respuesta salvo que se solicite detalle explicito.\n"
            '2. CERO MULETILLAS: Prohibido usar saludos ("Hola", "Claro", "Entendido", '
            '"Vale"), despedidas ("Quedo atento", "Un saludo"), o introducciones '
            '("Voy a", "Te comento que"). Ve DIRECTO a la informacion.\n'
            "3. TEXTO PLANO UNICAMENTE: Prohibido Markdown. No uses viñetas, asteriscos, "
            "negritas, codigo, tablas, emojis, ni formatos especiales. Escribe el texto "
            "exactamente como debe ser pronunciado por una voz humana natural.\n"
            "4. CONFIRMACION INMEDIATA: Cuando se solicite confirmar una accion "
            "(registrar inventario, procesar notas, ajustar hardware), inicia "
            "DIRECTAMENTE con la confirmacion y el resultado final.\n"
            'Ejemplo: "Listo, registre 3 cervezas y 2 aguas en mesa 5."\n'
            "5. NUMEROS NATURALES: Expresa numeros como se hablan, no como se escriben. "
            'Correcto: "trescientos cincuenta". Incorrecto: "350".\n'
            "6. SIN INFORMACION REDUNDANTE: No repitas lo que el usuario acaba de decir. "
            "No expliques tu razonamiento. Solo el resultado.\n"
            "EJEMPLOS DE RESPUESTAS CORRECTAS:\n"
            '- "Listo, anote 2 pastas y 1 ensalada para la mesa 3."\n'
            '- "El inventario de hoy: 45 cervezas, 30 vinos, 12 gaseosas."\n'
            '- "Reiniciando el router. Conexion restablecida en 30 segundos."\n'
            "EJEMPLOS DE RESPUESTAS PROHIBIDAS:\n"
            '- "Hola, con gusto te ayudo con eso. Voy a procesar tu solicitud..."\n'
            '- "**Confirmacion:** *Se ha registrado exitosamente*"\n'
            '- "Claro que si! A continuacion el detalle de tu pedido: 1. ... 2. ..."'
        )

    async def start(self):
        """Crea la sesion HTTP compartida con connection pooling."""
        connector = aiohttp.TCPConnector(limit=20, ttl_dns_cache=300)
        self._session = aiohttp.ClientSession(connector=connector)

    async def stop(self):
        """Cierra la sesion HTTP compartida."""
        if self._session:
            await self._session.close()
            self._session = None

    async def process_task(self, text_input: str) -> Dict[str, Any]:
        """
        Procesa una tarea y retorna la respuesta con metadatos.
        El formato de salida esta optimizado para TTS streaming.
        """
        start_time = time.time()

        # Dedup cache — misma query dentro de 300s devuelve resultado cacheado
        cache_key = hashlib.md5(f"{self.model}:{text_input}".encode()).hexdigest()
        if cache_key in self._query_cache:
            cached = self._query_cache[cache_key]
            return {
                "text": cached["content"],
                "model_used": cached["model"] + "+cache",
                "latency_ms": round((time.time() - start_time) * 1000, 2),
            }

        # 1. Seleccionar modelo via LiteLLM (routing automatico)
        try:
            response = await self._query_llm(text_input)
            content = response.get("content", "Error procesando peticion.")
            model_used = response.get("model", self.model)
            self._query_cache[cache_key] = {
                "content": self._sanitize_for_tts(content),
                "model": model_used,
            }
        except Exception as e:
            print(f"Error llamando a LiteLLM: {e}")
            content = f"Error al conectar con el router de lenguaje. {str(e)}"
            model_used = "local-fallback"

        # 2. Post-procesamiento: asegurar formato TTS-friendly
        clean_text = self._sanitize_for_tts(content)

        # 3. Log de la operacion
        latency_ms = round((time.time() - start_time) * 1000, 2)
        await self._log_execution(text_input, clean_text, model_used, latency_ms)

        return {"text": clean_text, "model_used": model_used, "latency_ms": latency_ms}

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8)
    )
    async def _query_llm(self, text_input: str) -> Dict[str, Any]:
        """Realiza la consulta asincrona al LiteLLM Proxy usando la sesion compartida."""
        url = f"{self.litellm_url}/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.litellm_key:
            headers["Authorization"] = f"Bearer {self.litellm_key}"

        messages = [{"role": "system", "content": self.system_prompt}]
        for hist in list(self.conversation_history)[-4:]:
            messages.append(hist)
        messages.append({"role": "user", "content": text_input})

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        session = self._session
        if session is None or session.closed:
            connector = aiohttp.TCPConnector(limit=20, ttl_dns_cache=300)
            session = aiohttp.ClientSession(connector=connector)
            owns_session = True
        else:
            owns_session = False

        try:
            async with session.post(
                url,
                headers=headers,
                data=orjson.dumps(payload),
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise Exception(f"HTTP {resp.status}: {error_text}")

                result = orjson.loads(await resp.read())
                content = result["choices"][0]["message"]["content"]
                model_name = result.get("model", self.model)

                self.conversation_history.append(
                    {"role": "user", "content": text_input}
                )
                self.conversation_history.append(
                    {"role": "assistant", "content": content}
                )

                return {"content": content, "model": model_name}
        finally:
            if owns_session:
                await session.close()

    def _sanitize_for_tts(self, text: str) -> str:
        """Sanitiza el texto eliminando Markdown y caracteres no pronunciables."""
        # Remover negritas, cursivas, codigo y headers de markdown
        text = re.sub(r"[*_`#\-\[\]()]+", "", text)

        # Reemplazar multiples espacios por uno solo
        text = re.sub(r"\s+", " ", text).strip()

        # Remover saludos y muletillas comunes en caso de que el modelo haya fallado en seguir el system prompt
        blacklist = [
            r"^hola,?\s*",
            r"^entendido,?\s*",
            r"^claro,?\s*",
            r"^vale,?\s*",
            r"^te comento que\s*",
            r"^un saludo\s*$",
            r"^quedo atento\s*$",
        ]
        for pattern in blacklist:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        # Reemplazar numeros simples por palabras si la expresion no es muy larga
        num_map = {
            "0": "cero",
            "1": "uno",
            "2": "dos",
            "3": "tres",
            "4": "cuatro",
            "5": "cinco",
            "6": "seis",
            "7": "siete",
            "8": "ocho",
            "9": "nueve",
            "10": "diez",
        }
        for num, word in num_map.items():
            text = re.sub(r"\b" + num + r"\b", word, text)

        return text.strip()

    async def _log_execution(
        self, query: str, response: str, model: str, latency: float
    ):
        """Registra la ejecucion en un archivo de log local y memoria (disk write en executor)."""
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "query": query,
            "response": response,
            "model": model,
            "latency_ms": latency,
        }
        self.execution_log.append(log_entry)

        if len(self.execution_log) > 100:
            self.execution_log.pop(0)

        def _write():
            os.makedirs(self.logs_dir, exist_ok=True)
            with open(os.path.join(self.logs_dir, "agent_execution.log"), "ab") as f:
                f.write(orjson.dumps(log_entry) + b"\n")

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, _write)
        except Exception as e:
            print(f"No se pudo escribir en log de ejecucion: {e}")
