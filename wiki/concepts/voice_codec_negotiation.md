---
name: "Voice Codec Negotiation"
type: concept
category: architecture
status: active
introduced_date: "2026-04-01"
last_reviewed: "2026-05-25"
---

# Voice Codec Negotiation

El proceso por el cual [[whisper_stt]] y [[hermes_agent]] acuerdan el formato de audio para la transcripcion. Define que codecs, sample rates y formatos de contenedor son aceptados.

## Por que existe

El audio capturado por el cliente puede llegar en distintos formatos (WAV, MP3, WebM, Opus). Whisper acepta varios formatos pero tiene preferencias de sample rate. La negociacion garantiza que el audio llegue en un formato que Whisper pueda procesar eficientemente.

## Como funciona

El cliente envia audio al [[hermes_agent]], que lo reenvía a [[whisper_stt]]. El formato recomendado es:
- **Codec:** PCM 16-bit (WAV) o Opus/WebM para menor tamano
- **Sample rate:** 16000 Hz (optimo para Whisper)
- **Canales:** Mono

Si el audio llega en otro formato, se realiza conversion antes de enviar a Whisper.

## Entidades relacionadas

- [[whisper_stt]] — receptor del audio, acepta el formato negociado
- [[hermes_agent]] — intermediario que puede realizar conversion de formato
- [[voice_pipeline_e2e]] — pipeline donde se aplica esta negociacion

## Trade-offs

- **Ganado:** flexibilidad en el formato de entrada del cliente, compatibilidad con distintos dispositivos.
- **Perdido:** conversion de formato anade latencia si el codec no es el optimo.

## Referencias

- [[voice_pipeline_e2e]] — contexto del pipeline completo
- [[whisper_stt]] — configuracion de modelos y formatos aceptados
