# Hermes Stack — Guion Narrativo para NotebookLM

**Documento complementario al blueprint técnico.**
Diseñado para que NotebookLM, ingiriéndolo junto al PDF `Hermes_Stack_Blueprint.pdf`, genere un video tutorial coherente, didáctico y memorable sobre el pipeline end-to-end del Hermes Stack.

- Autor: Erik José Hernández
- Fecha: 23 de mayo de 2026
- Idioma: español neutro
- Tono recomendado para la narración: conversacional, claro, con pausas analíticas y analogías concretas
- Duración objetivo del video resultante: 15 a 20 minutos

---

## Propósito de este documento

Este guion no repite el blueprint. Lo traduce. El blueprint es el plano técnico denso —tablas, diagramas, configuraciones, healthchecks—. Este guion es el storyboard hablado: la versión narrativa que un humano contaría a otro humano en una sala de reuniones, frente a una pizarra. NotebookLM debe usar ambos: el blueprint como **fuente de verdad**, este documento como **estructura del relato**.

Cada sección está pensada como un capítulo del video. Los títulos pueden funcionar como rótulos en pantalla. Los pasajes en cursiva entre paréntesis son **acotaciones visuales sugeridas** para que NotebookLM proponga slides, no para ser leídas.

---

## 1. Hook — el problema que resuelve el Hermes Stack

Imagina que hablas en voz alta y, medio segundo después, una inteligencia artificial te responde con voz natural, recordando lo que dijiste hace cinco minutos, consultando herramientas externas si hace falta, y todo ello corriendo en un único servidor virtual privado al que tú —y solo tú— controlas. Sin APIs propietarias atándote. Sin un proveedor único que pueda apagar tu acceso. Sin telemetría escapándose hacia compañías que no conoces.

Eso es el Hermes Stack.

*(Visual: una persona hablando a su teléfono, una nube tachada con una equis roja, y un servidor físico iluminado con un logo "el80.space" sobre él.)*

El Hermes Stack es una infraestructura de inteligencia artificial autohospedada, modular y declarativa. Combina diez microservicios coordinados con Docker Compose para ofrecer un agente conversacional por voz, multimodelo, observado en tiempo real y con auto-curación. Está pensado para una persona o un equipo pequeño que quiera **propiedad total** sobre su stack de IA sin sacrificar latencia ni calidad.

El reto técnico central es brutal: que el ciclo completo —desde que terminas de hablar hasta que escuchas la primera sílaba de la respuesta— ocurra en **menos de quinientos milisegundos**. Ese es el umbral del pulso humano, el límite por debajo del cual una conversación se siente natural. Por encima, se siente como un asistente de hace diez años.

---

## 2. Visión general en sesenta segundos

Antes de bajar a los detalles, fijemos el mapa.

En el centro hay un servidor virtual. Sobre él corre Docker, que orquesta diez contenedores. Cuatro de esos contenedores son **públicos** —accesibles desde internet a través de subdominios HTTPS bajo `el80.space`—: el agente Hermes, el proxy LiteLLM, el dashboard Grafana y el sitio web del proyecto. El resto son **internos**: Redis, Whisper, Prometheus, cAdvisor, Node Exporter y un proceso silencioso llamado Autoheal.

El tráfico externo entra por un único portero: **Caddy**, un reverse proxy que también administra los certificados SSL de Let's Encrypt automáticamente. Caddy decide a qué subdominio responde y reenvía la petición al contenedor correspondiente.

Por dentro, los servicios hablan entre sí a través de dos redes Docker aisladas: una de **backend** y otra de **monitoring**. Ningún servicio interno está expuesto al mundo. Solo Caddy.

*(Visual: diagrama de bloques con Caddy en la parte superior, los cuatro subdominios bajando hacia sus respectivos contenedores, y las dos redes Docker como nubes coloreadas conectando todo.)*

Ahora sí, entremos al recorrido.

---

## 3. El recorrido de una conversación: del aire al algoritmo y vuelta al aire

Esta es la sección central del video. Vamos a seguir, paso a paso, qué le pasa a una frase tuya desde que sale de tu boca hasta que escuchas la respuesta del agente.

### 3.1 Etapa 1 — captura del audio

Todo empieza con un micrófono. En el cliente —puede ser una página web, una app móvil futura, o un terminal de voz embebido— se abre un canal de audio. La aplicación cliente abre un WebSocket contra `hermes.el80.space` y empieza a empujar fragmentos PCM de aproximadamente veinte milisegundos cada uno.

*(Visual: ondas de sonido entrando a un micrófono, animadas como pequeñas burbujas que se desprenden y vuelan hacia un servidor.)*

Aquí ya hay una decisión arquitectónica importante: no se espera a que el usuario termine de hablar. Se transmite **en tiempo real**. Eso recorta latencia porque la transcripción puede empezar antes de que termine la frase.

### 3.2 Etapa 2 — Whisper STT: del audio al texto

Los fragmentos llegan a un contenedor interno llamado `whisper-stt`. Es una instancia local del modelo Whisper de OpenAI, pero ejecutándose **íntegramente en el servidor**, sin enviar ni un byte de tu voz a un tercero.

Whisper es como un mecanógrafo invisible y multilingüe que escucha el audio en streaming y produce texto parcial. Cuando detecta una pausa significativa —un silencio de más de unos cientos de milisegundos—, emite un evento de "transcripción final".

*(Visual: una ola de sonido entrando a una caja con el logo de OpenAI Whisper y saliendo como texto en una burbuja de chat.)*

El texto final se envía al siguiente eslabón: el agente Hermes.

### 3.3 Etapa 3 — Hermes Agent: el cerebro orquestador

Hermes es el contenedor más importante del stack. Es un proceso Python, expuesto en el puerto interno ocho mil ochenta, que coordina toda la lógica conversacional. Si el stack fuera una orquesta, Hermes sería el director.

¿Qué hace Hermes exactamente?

Primero, **recibe el texto** de Whisper. Después **consulta su memoria**: usa Redis, un servicio interno de caché de alto rendimiento, para recuperar el contexto de la conversación —los mensajes anteriores, el estado de la sesión, las preferencias del usuario—. Hermes también puede invocar **herramientas externas**: APIs, bases de datos, scripts. Esto es lo que en la jerga se llama "function calling" o "tool use": el agente decide, según el contenido del mensaje, si necesita ayuda externa antes de pensar la respuesta.

Una vez tiene la pregunta y el contexto preparados, Hermes no llama directamente a un modelo de lenguaje. Llama a un intermediario inteligente: **LiteLLM**.

*(Visual: un personaje tipo director de orquesta con batuta, varias partituras en el atril que representan "memoria", "herramientas" y "modelos", y flechas saliendo hacia los siguientes contenedores.)*

### 3.4 Etapa 4 — LiteLLM: el conmutador inteligente de modelos

LiteLLM es probablemente la pieza más subestimada de este stack. Es un proxy unificado que habla el mismo protocolo que la API de OpenAI, pero detrás puede enrutar a cualquier proveedor: OpenRouter, Gemini directo, Anthropic, modelos locales con Ollama, lo que sea.

¿Por qué existe? Porque depender de un único proveedor de modelos es un suicidio operacional. Si el día que más necesitas tu asistente OpenAI tiene una caída, o aumenta los precios un treinta por ciento, o cambia las políticas de uso, tu agente se queda mudo.

LiteLLM resuelve eso con una sola configuración. Tú declaras qué modelos quieres, en qué orden de prioridad, y LiteLLM se encarga del failover automático. Si un proveedor falla, salta al siguiente sin que Hermes se entere.

*(Visual: una operadora telefónica de los años cincuenta enchufando cables entre clavijas etiquetadas "OpenRouter", "Gemini", "Anthropic", "Ollama local".)*

Otro detalle clave: LiteLLM se expone públicamente en `litellm.el80.space`, lo que significa que **cualquier otra aplicación del portafolio** —presente o futura— puede usarlo como su backend de LLM. No solo Hermes. Esto convierte al Hermes Stack en una plataforma, no en una aplicación monolítica.

Y para protegerlo, el endpoint público exige una **master key** —`LITELLM_MASTER_KEY`— que viaja en el archivo `.env` del servidor y nunca se commitea. El health check del propio pipeline de despliegue se autentica con esa clave para verificar que el servicio responde.

### 3.5 Etapa 5 — OpenRouter o Gemini: el razonamiento profundo

LiteLLM resuelve a quién llamar. Hoy, por defecto, hay dos rutas configuradas: OpenRouter como agregador con docenas de modelos disponibles, y Gemini como ruta directa a los modelos de Google. El modelo activo puede cambiarse sin tocar ni una línea del agente Hermes: solo se edita la configuración de LiteLLM.

El modelo recibe el prompt completo —instrucción de sistema, historial, mensaje del usuario, descripción de herramientas disponibles— y devuelve una respuesta. Puede ser texto plano, o puede ser una **invocación de herramienta** ("oye, llama a esta API antes de responder"). Hermes lo gestiona y, eventualmente, obtiene la respuesta textual final.

*(Visual: nubes de los proveedores —OpenRouter, Google AI— recibiendo un sobre con la pregunta y devolviendo otro sobre con la respuesta.)*

### 3.6 Etapa 6 — ElevenLabs Flash v2.5: la voz que responde

La respuesta es texto. Pero el usuario espera voz. Aquí entra el último eslabón: **ElevenLabs Flash v2.5**, conectado vía WebSocket.

¿Por qué WebSocket y no HTTP convencional? Porque el WebSocket permite **streaming bidireccional**: Hermes empuja el texto a medida que lo recibe del modelo —no hace falta esperar la frase completa— y ElevenLabs empuja audio de vuelta a medida que lo genera. El primer fragmento de audio puede empezar a sonar cuando todavía no se ha generado la última palabra del texto.

Flash v2.5 es el modelo de baja latencia de ElevenLabs, optimizado para conversación en tiempo real. La voz se identifica por un `ELEVENLABS_VOICE_ID` configurado en el `.env`. Puede personalizarse para que el agente tenga una identidad sonora consistente —tu propia marca de voz si lo deseas, o una voz preestablecida del catálogo—.

*(Visual: un actor de doblaje sintético frente a un micrófono, con ondas de voz saliendo en cascada y volviendo al usuario inicial.)*

### 3.7 Latencia total — el reto del medio segundo

Sumemos las etapas en el mejor caso:

- Captura y envío del audio: cuarenta milisegundos
- Whisper STT en streaming: cien a ciento cincuenta milisegundos
- Hermes Agent + Redis lookup: treinta milisegundos
- LiteLLM → modelo → primer token: cien a doscientos milisegundos
- ElevenLabs Flash v2.5 primera sílaba: ochenta a cien milisegundos

Total: entre trescientos cincuenta y quinientos veinte milisegundos. Justo en el límite. Por eso el diseño es tan agresivo en streaming bidireccional, caché de Redis y modelos de baja latencia. Cada milisegundo cuenta.

*(Visual: un cronómetro digital marcando "500 ms" en rojo, con una barra de progreso descomponiendo cada etapa.)*

---

## 4. La capa invisible — observabilidad continua

Hasta aquí hemos visto el flujo principal, el camino "feliz" de una conversación. Pero un sistema de producción no se trata solo del camino feliz. Se trata de **saber qué está pasando** cuando algo no va bien. Esa es la capa de observabilidad.

### 4.1 Prometheus

Prometheus es el corazón métrico del stack. Es un servidor de series temporales que cada quince segundos consulta —"scrapea"— a todos los servicios que exponen métricas: Hermes, LiteLLM, Redis, los nodos Docker, el host. Almacena cada valor con un timestamp.

Las métricas típicas incluyen: peticiones por segundo, latencia P50/P95/P99, uso de CPU y memoria por contenedor, errores por endpoint, tokens consumidos por modelo. Todo eso queda registrado de forma persistente.

*(Visual: un electrocardiograma del sistema, con varias líneas de colores ascendiendo y descendiendo.)*

### 4.2 Grafana

Grafana es la cara visible de Prometheus. Es un dashboard configurable expuesto en `grafana.el80.space`, donde puedes visualizar cualquiera de esas métricas en tiempo real, con paneles, alertas, comparativas temporales y zoom.

Grafana es a Prometheus lo que un panel de mandos es a la centralita eléctrica de un edificio. Sin Grafana, las métricas existen pero no las puedes leer cómodamente.

### 4.3 cAdvisor y Node Exporter

cAdvisor y Node Exporter son los **sensores**. cAdvisor mide cada contenedor Docker individualmente —cuánta CPU consume, cuánta memoria, cuánta red—. Node Exporter mide el host completo —el disco, la temperatura, los procesos del sistema operativo—.

Sin estos dos, Prometheus no tendría qué scrapear. Son los ojos y oídos a nivel de infraestructura.

---

## 5. La capa silenciosa — auto-curación

Saber qué pasa es útil. **Actuar automáticamente** cuando algo falla es transformador. Esa es la capa de auto-curación.

### 5.1 Healthchecks declarativos

Cada servicio del `docker-compose.yml` define un **healthcheck**: un comando que Docker ejecuta periódicamente —típicamente cada treinta segundos— para verificar que el contenedor sigue sano. Si el comando devuelve éxito, el contenedor se marca como `healthy`. Si falla varias veces consecutivas, se marca como `unhealthy`.

Por ejemplo, el healthcheck de Hermes es un simple `curl -f http://localhost:8080/health`. El de LiteLLM hace lo propio contra su endpoint de salud. Cada servicio define su propio "estoy vivo".

### 5.2 Autoheal

Aquí viene la magia. Hay un contenedor especial llamado `autoheal` cuya única misión es vigilar a los demás. Cada treinta segundos, escanea todos los contenedores marcados con la etiqueta `autoheal.enabled: "true"`. Si encuentra uno en estado `unhealthy`, lo **reinicia automáticamente**, sin intervención humana.

Esto cubre la inmensa mayoría de fallos transitorios: un proceso que se quedó colgado, una conexión a Redis que se rompió, un picho de memoria que mató al worker. El sistema se cura solo.

*(Visual: una célula del sistema inmunológico identificando una célula enferma y reemplazándola.)*

### 5.3 Watchdog

Pero ¿qué pasa si Autoheal mismo se cae? ¿O si Docker se cae? Para eso hay un script externo: `docker-watchdog.sh`. Es un demonio nivel host que vigila al propio Docker. Si Docker no responde, lo reinicia con `systemctl restart docker`. Es el sistema inmunológico del sistema inmunológico.

---

## 6. La capa pública — Caddy y los subdominios

Volvamos a la puerta de entrada. Caddy es un reverse proxy moderno escrito en Go. Hace tres cosas críticas:

Primero, **gestiona el TLS automáticamente**. No hay que configurar certificados, no hay que renovarlos manualmente, no hay que reiniciar nada cuando expira un certificado de Let's Encrypt. Caddy lo hace solo, en silencio, gracias al protocolo ACME y a un bloque global del Caddyfile donde se declara el email de contacto:

```
{
    email erikjosehernandez@gmail.com
}
```

Segundo, **enruta los subdominios** al contenedor correcto:

| Subdominio | Backend interno | Servicio |
|---|---|---|
| `hermes.el80.space` | `127.0.0.1:8080` | Agente Hermes |
| `litellm.el80.space` | `127.0.0.1:4000` | LiteLLM Proxy |
| `grafana.el80.space` | `127.0.0.1:3000` | Grafana |
| `docs.el80.space` | `127.0.0.1:3001` | Sitio web Hermes |

Tercero, **redirige HTTP a HTTPS** sin que tengamos que configurarlo: por defecto Caddy lo hace.

*(Visual: un portero de hotel con uniforme negro y placa "Caddy" recibiendo varios visitantes y dirigiéndolos a habitaciones numeradas según su gafete.)*

El firewall del servidor —UFW— solo permite tráfico en los puertos 80 y 443 hacia el exterior. Todo el resto es bind a `127.0.0.1`, inaccesible desde fuera. Defense in depth.

---

## 7. La capa del portafolio — el sitio web docs.el80.space

El servicio que sirve `docs.el80.space` es un sitio web pequeño pero notable. Es una aplicación React 18 construida con Vite, estilada con Tailwind y animada con Framer Motion. La parte visible —la landing— tiene un hero animado, una grilla de servicios disponibles, estadísticas en vivo y un visor en árbol del repositorio.

Detrás del React hay un servidor Express minimalista que expone dos endpoints internos: `/api/tree`, que recorre el sistema de archivos del proyecto y devuelve un árbol JSON con profundidad limitada y filtrado de archivos ocultos, y `/health` para el monitoreo.

El contenedor monta el directorio `/root` del host **en modo solo lectura** —`/root:/host-root:ro`—. Esto significa que el sitio web puede mostrar la estructura del repositorio pero no puede modificarla. Defensa contra movimientos laterales.

*(Visual: una persona navegando una página web oscura, hover sobre una tarjeta que dice "Hermes Agent" con un dot verde palpitante.)*

Este sitio es la **fachada del portafolio**. Es lo que ve un visitante curioso, un cliente potencial, o un reclutador técnico que llega a `el80.space`. Es la prueba pública de que el stack existe y funciona.

---

## 8. La capa de DevOps — CI/CD desde GitHub Actions

Hasta ahora hemos hablado de cómo funciona el stack en runtime. Pero un sistema también se trata de **cómo evoluciona**. Aquí entra el pipeline de despliegue.

Cada vez que se hace `git push` a la rama `main` del repositorio en GitHub, se dispara un workflow en GitHub Actions. El workflow:

1. Hace checkout del código.
2. Ejecuta linters y type checks.
3. Se conecta por SSH al VPS usando una clave privada almacenada en GitHub Secrets.
4. Ejecuta `git pull origin main` en `/root` del servidor.
5. Levanta los contenedores con `docker compose up -d --build`.
6. Espera quince segundos.
7. Ejecuta health checks autenticados: uno contra LiteLLM (con la master key), otro contra Hermes.
8. Si algún health check falla, hace **rollback automático**: `git checkout HEAD~1 && docker compose up -d --build` y termina con código de error.

*(Visual: un commit verde en GitHub, una flecha hacia abajo, ocho engranajes girando en secuencia, y al final un check verde grande con "Deploy OK" o, en caso de fallo, un rollback rojo con "Reverted to HEAD~1".)*

Es un pipeline simple pero efectivo. Sus limitaciones conocidas: el rollback solo cubre un commit, los secretos viven plaintext en el `.env` del VPS, y el sleep fijo de quince segundos podría ser un retry exponencial más elegante. Son áreas claras de mejora futura.

---

## 9. El siguiente capítulo — la app nativa Android desde Google AI Studio

Hasta aquí, el stack es accesible vía web y vía WebSocket. Pero la siguiente pieza del portafolio es una **app nativa Android**, construida con Kotlin y Jetpack Compose, generada inicialmente con Google AI Studio.

La app no reemplaza el stack. Lo complementa. Es el cliente móvil de primera clase para el Hermes Agent, optimizado para uso por voz en movimiento.

Sus módulos previstos son:

- `:feature-voice` para capturar audio del micrófono y streamear al stack.
- `:feature-chat` para la conversación textual y el historial.
- `:feature-tools` para invocar manualmente las herramientas del agente.
- `:feature-observability` para mostrar un panel resumen de Grafana embebido vía WebView.
- `:feature-settings` para configurar endpoints y autenticación.

La autenticación contra el stack será por **token bearer firmado**, derivado en el servidor y rotado periódicamente. La app jamás verá la `LITELLM_MASTER_KEY`; recibirá un token de corta vida con scope limitado.

Sobre la red, la app aplicará **certificate pinning** contra `*.el80.space`, denegará tráfico en claro, y guardará los tokens en `EncryptedSharedPreferences`. Cumplirá Network Security Config estricta.

La integración con Google AI Studio permite además que parte del razonamiento de baja latencia ocurra **en el dispositivo**: Gemini Nano puede manejar interacciones triviales sin un viaje de ida y vuelta al servidor. Solo cuando la pregunta supera cierto umbral de complejidad, la app llama al Hermes Stack remoto.

*(Visual: un teléfono Android con la app abierta, micrófono pulsante, y una línea conectándolo con el servidor `el80.space` en la nube.)*

El roadmap propuesto:

- **Q3 2026**: MVP funcional con voz + chat.
- **Q4 2026**: lanzamiento público en Play Store con widgets de homescreen.
- **2027**: companion para Wear OS y soporte de tareas en background.

---

## 10. Glosario hablado

Para asegurar que la narración no se pierda en jerga, aquí está el vocabulario clave con definiciones de una frase. NotebookLM puede usarlo como overlay textual cuando aparezca cada término.

| Término | Definición en una frase |
|---|---|
| Docker Compose | Una receta declarativa que describe múltiples contenedores y sus relaciones en un solo archivo YAML. |
| Reverse proxy | Un servidor que recibe peticiones externas y las reenvía a servicios internos. |
| Let's Encrypt | Una autoridad certificadora gratuita que emite certificados SSL automáticamente vía el protocolo ACME. |
| WebSocket | Un canal de comunicación bidireccional sobre HTTP que permite streaming continuo. |
| Healthcheck | Un comando periódico que verifica si un servicio responde correctamente. |
| Failover | El cambio automático a un proveedor de respaldo cuando el primario falla. |
| Streaming bidireccional | Enviar y recibir datos simultáneamente, sin esperar a que termine el envío para empezar la recepción. |
| Function calling | La capacidad de un modelo de lenguaje para invocar funciones externas durante su razonamiento. |
| Certificate pinning | Una técnica que asocia un cliente con un certificado SSL específico para prevenir ataques man-in-the-middle. |
| ACME | El protocolo estándar para automatizar la emisión y renovación de certificados SSL. |

---

## 11. Llamada a la acción

Si has llegado hasta aquí, ya tienes una imagen completa del Hermes Stack. No es un proyecto académico. Es una plataforma viva, desplegada, con observabilidad, auto-curación y un pipeline de despliegue continuo. Y va a seguir creciendo: la app Android está en cola, y detrás vendrán más canales de voz, multitenancy, modelos locales fine-tuned.

El código vive en `github.com/erikjosehrnndz/hermes-stack`. La demo pública en `hermes.el80.space`. La documentación —este mismo blueprint— en `docs.el80.space`.

Si lo encuentras valioso, contribuye con ideas, prueba la demo, o úsalo como referencia para tu propio stack. La invitación está abierta.

---

## Notas de producción para NotebookLM

Si vas a generar **Audio Overview** (diálogo entre dos voces):
- Asigna a la voz A el rol de "narrador experto" que conduce el recorrido.
- Asigna a la voz B el rol de "curioso técnico" que hace preguntas aclaratorias en cada etapa.
- Las preguntas naturales que la voz B puede formular: "Espera, ¿por qué streaming bidireccional?", "¿Qué pasa si Autoheal falla?", "¿Cuál es el riesgo de usar un solo proveedor de LLM?".

Si vas a generar **Video Overview** (slides narrados):
- Usa los títulos de sección (## y ###) como rótulos de slides.
- Usa las acotaciones visuales entre paréntesis (en cursiva) como prompts para generar las imágenes/iconografía de cada slide.
- Mantén el tono conversacional pero más pausado que en audio puro: deja respirar cada concepto.

Si vas a generar un **resumen ejecutivo escrito**, prioriza las secciones 2 (visión general) y 3 (recorrido del pipeline), seguidas de 9 (Android) como gancho hacia el futuro.

---

**Fin del guion.**
