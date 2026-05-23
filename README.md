# 🎙️ Hermes Stack: El Mensajero Ultra-Rápido de la IA

> **"Hermes: El dios griego mensajero de la velocidad, la elocuencia y el habla. Este stack es el canal más rápido y seguro entre el pensamiento de la IA y la voz humana."**

[![Docker - 9 Containers](https://img.shields.io/badge/Docker-9%20Containers-blue?style=for-the-badge&logo=docker)](https://github.com/erikjosehrnndz-crypto/hermes-stack)
[![Latency - Under 700ms](https://img.shields.io/badge/Latency-%3C%20700ms-brightgreen?style=for-the-badge&logo=speedtest)](https://github.com/erikjosehrnndz-crypto/hermes-stack)
[![Security - Hardened](https://img.shields.io/badge/Security-Hardened%20%26%20Isolated-red?style=for-the-badge&logo=shield)](https://github.com/erikjosehrnndz-crypto/hermes-stack)
[![SSL - Caddy HTTPS](https://img.shields.io/badge/SSL-Automatic%20HTTPS-orange?style=for-the-badge&logo=letsencrypt)](https://github.com/erikjosehrnndz-crypto/hermes-stack)

Este repositorio contiene la arquitectura operativa de **ultra-baja latencia** diseñada para soportar comunicación bidireccional por voz con Inteligencia Artificial. Alcanza tiempos de respuesta de **voz a voz en menos de 700ms** combinando enrutamiento inteligente, caché de latencia y servicios locales.

---

## ⚡ El Viaje de tu Voz (Flujo en < 700ms)

¿Cómo procesa el sistema tu voz tan rápido? Aquí está el recorrido simplificado de una consulta:

```
  🎙️ TU VOZ ➔ [ 1. Oído: Whisper STT ] ➔ Transcribe el audio a texto localmente
                                    ↓
  🧠 TEXTO   ➔ [ 2. Cerebro: Agente Hermes ] ➔ Lógica del negocio y contexto
                                    ↓
  🔀 DECISIÓN➔ [ 3. Enrutador: LiteLLM ] ➔ Elige el modelo de IA más rápido (Claude 4.6)
                                    ↓
  🗣️ RESPUESTA ➔ [ 4. Voz: ElevenLabs ] ➔ Genera y transmite audio por streaming WebSocket
```

---

## 🗺️ Mapa Visual de Conexiones (Arquitectura)

Así es como se comunican todos los componentes del sistema dentro de tu servidor VPS:

```mermaid
flowchart TD
    %% Estilos de Nodos
    classDef external fill:#f9f,stroke:#333,stroke-width:2px,color:#000;
    classDef security fill:#f96,stroke:#333,stroke-width:2px,color:#000;
    classDef core fill:#69c,stroke:#333,stroke-width:2px,color:#fff;
    classDef monitoring fill:#9c6,stroke:#333,stroke-width:2px,color:#000;

    %% Clientes y Entrada
    Usuario([🎙️ Usuario / Cliente de Voz]) -- HTTPS / WSS --> Caddy[🔒 Caddy Reverse Proxy\nPuertos: 80 / 443]
    Tailscale([🔑 Tailscale VPN\nAcceso Admin]) -. Conexión Segura .-> Host

    %% Host VPS
    subgraph Host [🖥️ VPS Host: 172.236.102.166]
        Caddy:::security --> Hermes[🧠 Agente Hermes\n127.0.0.1:8080]:::core
        Caddy:::security --> LiteLLM[🔀 LiteLLM Router\n127.0.0.1:4000]:::core
        Caddy:::security --> Grafana[📊 Grafana Dashboards\n127.0.0.1:3000]:::monitoring
    end

    %% Capa Docker Aislada
    subgraph DockerNet [🐳 Red Docker Interna e Aislada]
        Hermes --> LiteLLM
        Hermes --> Whisper[👂 Whisper STT Local\nPuerto: 9000]:::core
        Hermes -- Streaming de Audio --> ElevenLabs[[🗣️ ElevenLabs WS\nAPI Externa]]:::external
        
        LiteLLM --> Redis[(💾 Redis Cache\nVelocidad)]:::core
        LiteLLM --> IAExternas[[🤖 OpenRouter / Gemini\nModelos de IA]]:::external
        
        %% Monitoreo
        Prometheus[📈 Prometheus Server\nPuerto: 9090]:::monitoring --> Hermes
        Prometheus --> LiteLLM
        Prometheus --> NodeExporter[🖥️ Node Exporter\nMétricas Host]:::monitoring
        Prometheus --> cAdvisor[🐳 cAdvisor\nMétricas Contenedores]:::monitoring
        Grafana --> Prometheus
        
        %% Guardianes
        Autoheal[🩺 Autoheal\nAuto-Reinicio]:::security -. Monitorea salud .-> Hermes & LiteLLM
        Watchdog[🐕 Systemd Watchdog]:::security -. Vigila daemon Docker .-> DockerNet
    end

    %% Aplicar clases
    class Usuario,ElevenLabs,IAExternas external;
```

---

## 🛠️ ¿Qué compone el Sistema? (Los 3 Pilares)

### 🧱 Pilar 1: Procesamiento e Inteligencia
| Servicio | Ícono | Nombre Técnico | ¿Qué hace? (Explicado Simple) |
| :--- | :---: | :--- | :--- |
| **El Cerebro** | 🧠 | `hermes-agent` | Procesa lo que dices, maneja la memoria de la conversación y envía el texto limpio para ser sintetizado a voz. |
| **El Oído** | 👂 | `whisper-stt` | Transcribe tu voz a texto de forma 100% local en tu servidor (cero costo de red). |
| **El Enrutador** | 🔀 | `litellm-router` | Elige inteligentemente qué IA responde (Claude 4.6 Sonnet, GPT-4o, etc.) basándose en cuál es más rápida en ese instante. |
| **La Memoria Flash** | 💾 | `redis-cache` | Guarda en caché respuestas anteriores para responder al instante sin consultar a la IA. |

### 🛡️ Pilar 2: Seguridad y Redes
| Servicio | Ícono | Nombre Técnico | ¿Qué hace? (Explicado Simple) |
| :--- | :---: | :--- | :--- |
| **El Portero** | 🔒 | `Caddy` | Servidor web que recibe a los usuarios en `el80.space`, les da certificados SSL (HTTPS) y los conecta de forma segura hacia el agente. |
| **La Muralla** | 🧱 | `IPTables` | Bloquea que cualquier persona en internet acceda directamente a las bases de datos o servicios internos de Docker. |
| **El Túnel Privado** | 🔑 | `Tailscale` | Una red privada (VPN) para que tú y tu equipo accedan de forma segura a la administración del servidor. |

### 📈 Pilar 3: Monitoreo y Recuperación
| Servicio | Ícono | Nombre Técnico | ¿Qué hace? (Explicado Simple) |
| :--- | :---: | :--- | :--- |
| **El Inspector** | 📈 | `prometheus` | Recolecta estadísticas de velocidad, CPU, memoria y errores del sistema cada segundo. |
| **El Panel de Control** | 📊 | `grafana` | Dibuja gráficos bonitos en tiempo real de cómo se comporta tu servidor. |
| **El Médico** | 🩺 | `autoheal` | Si detecta que el agente Hermes o LiteLLM se traban, los reinicia automáticamente. |
| **El Perro Guardián** | 🐕 | `docker-watchdog` | Servicio de Linux que vigila que Docker esté corriendo bien en el servidor. |

---

## 🕹️ Guía de Comandos Rápidos (Operaciones)

Ejecuta estos comandos en la terminal de tu VPS (`/root`):

### 🟢 Encender el Stack
```bash
docker compose up -d
```

### 🔴 Apagar el Stack
```bash
docker compose down
```

### 🔄 Reiniciar un Componente (Ej: El Cerebro)
```bash
docker compose restart hermes
```

### 🩺 Ver si todo está Saludable
```bash
docker ps
```
*(Verás la palabra `(healthy)` al lado de cada servicio).*

---

## 🌍 Acceso a tus Servicios en Producción

Todos tus servicios están protegidos bajo tu dominio público con certificados de seguridad HTTPS:

* 🧠 **API del Agente:** [https://hermes.el80.space/health](https://hermes.el80.space/health)
* 🔀 **Router LiteLLM:** [https://litellm.el80.space](https://litellm.el80.space)
* 📊 **Estadísticas Grafana:** [https://grafana.el80.space](https://grafana.el80.space)
