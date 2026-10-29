import json
import urllib.error
import urllib.request

BASE = "http://localhost:11434"
MODEL = "llama3.2:3b"

def ollama_status():
    try:
        with urllib.request.urlopen(BASE + "/api/tags", timeout=2) as response:
            models = json.loads(response.read()).get("models", [])
        present = any(m.get("name", "").split(":")[0] == MODEL.split(":")[0] and m.get("name", "").endswith(":3b") for m in models)
        return True, present, "Ollama local REST API reachable. " + ("Model is installed." if present else f"Install with: ollama pull {MODEL}")
    except (OSError, urllib.error.URLError, ValueError):
        return False, False, "Start Ollama locally to enable model answers; retrieval fallback works without it."

def generate(prompt: str, on_chunk=None) -> str:
    body = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "stream": on_chunk is not None,
        "keep_alive": "10m",
        "options": {
            "num_ctx": 4096,
            "num_predict": 160,
            "temperature": 0.15,
        },
    }).encode()
    request = urllib.request.Request(BASE + "/api/generate", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=120) as response:
        if on_chunk is None:
            return json.loads(response.read()).get("response", "").strip()

        chunks = []
        for line in response:
            if not line.strip():
                continue
            token = json.loads(line).get("response", "")
            if token:
                chunks.append(token)
                on_chunk(token)
        return "".join(chunks).strip()
