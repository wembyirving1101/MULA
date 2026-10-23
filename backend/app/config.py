import os


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "huihui_ai/qwen3-abliterated:latest")

# Keep a modest context and bounded replies for a responsive local chat.
OLLAMA_KEEP_ALIVE = os.getenv("OLLAMA_KEEP_ALIVE", "15m")
OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "4096"))
OLLAMA_NUM_PREDICT = int(os.getenv("OLLAMA_NUM_PREDICT", "384"))
if OLLAMA_NUM_CTX < 1024 or OLLAMA_NUM_PREDICT < 1:
    raise ValueError("OLLAMA_NUM_CTX must be >= 1024 and OLLAMA_NUM_PREDICT must be positive.")
