# ARIA self-hosted inference

This deployment exposes a trained or base model through vLLM's OpenAI-compatible API. It requires Linux, a supported NVIDIA GPU, Docker, and the NVIDIA container runtime.

```bash
ARIA_MODEL_PATH=/models/aria-qwen-lora-smoke docker compose \
  -f serving/vllm/docker-compose.vllm.yml up -d
curl http://localhost:8001/health
```

For an unmerged LoRA adapter, configure the vLLM LoRA arguments for the installed vLLM release. Validate adapter support and pin the image before promotion. ARIA application traffic should use Envoy AI Gateway rather than bypassing the gateway.

The Mac development path uses LoRA training and Ollama or Transformers inference. QLoRA and this vLLM profile are intended for the ASUS machine only if its NVIDIA GPU and CUDA version are supported, or for a temporary cloud GPU.
