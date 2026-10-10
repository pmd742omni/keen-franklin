# Open-Source LLM Runtimes: Ollama, vLLM, and llama.cpp (2026)

> Technical reference for self-hosting open-weight models (Llama 3.x, Mistral, Qwen 2.5) with zero third-party API costs.

---

## 1. Runtime Comparison for Self-Hosted AI

| Engine | Concurrency Model | Hardware Target | Best Suited For | Key Differentiator |
|---|---|---|---|---|
| **vLLM** | Continuous PagedAttention | High-End GPUs (NVIDIA A100/H100, RTX 4090) | High-throughput production APIs | 5x-10x throughput via PagedAttention memory management |
| **Ollama** | Single-Model Daemon | CPU, Apple Silicon, Single Consumer GPU | Development & edge application servers | 1-command model pull (`ollama run llama3.2`) and OpenAI-compatible API |
| **llama.cpp** | Native C/C++ Engine | CPU-only, low-spec VPS, embedded systems | Resource-constrained VPS and laptops | Zero GPU dependency with GGUF quantization (Q4_K_M, Q8_0) |

---

## 2. Deploying Ollama with Docker Compose

Running a private local AI service alongside web backends:

```yaml
# docker-compose.ai.yml
services:
  ollama:
    image: ollama/ollama:latest
    restart: unless-stopped
    ports:
      - "11434:11434"
    volumes:
      - ollama_models:/root/.ollama
    # Enable NVIDIA GPU pass-through if available:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

volumes:
  ollama_models:
```

---

## 3. OpenAI-Compatible API Consumption

Self-hosted engines expose endpoints adhering strictly to `/v1/chat/completions`, allowing seamless drop-in replacement in existing web backends:

```bash
# Streaming inference from local Ollama container
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2",
    "messages": [{"role": "user", "content": "Explain reactive programming."}],
    "stream": true
  }'
```
