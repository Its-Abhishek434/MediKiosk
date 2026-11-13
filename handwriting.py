"""
handwriting.py - handwriting transcription with a vision AI model. The model ONLY
transcribes; medscan.py then validates against drugs.csv / labs.csv.

Backends (choose with HANDWRITING_BACKEND):
  local  (default) - model running on YOUR machine via Ollama (http://localhost:11434).
  api              - Anthropic cloud API.
"""
import base64, json, os, re, urllib.request

BACKEND = os.environ.get("HANDWRITING_BACKEND", "local")
# Default model updated to Qwen3-VL:4B for superior spatial reasoning
MODEL = os.environ.get("HANDWRITING_MODEL", "claude-sonnet-5-5" if BACKEND == "api" else "qwen3-vl:4b")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
MEDIA = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}

PROMPT = """Transcribe this handwritten medical document EXACTLY as written, line by line.
Rules:
- Do NOT correct spelling, complete drug names, or guess doses. Copy what you see.
- If any character or word is unclear, write [?] in its place. Never guess.
- Keep abbreviations as written (OD, BD, 1-0-1, x 5d, etc.).
- Set "certain" to false for any line where you had doubt.
Return ONLY a JSON list, no other text: [{"text": "...", "certain": true}, ...]"""

# Max side scaled down to 1024 to prevent KV cache explosion on 4GB VRAM
MAX_SIDE = int(os.environ.get("HANDWRITING_MAX_SIDE", "1024")) 

def _b64(path):
    ext = os.path.splitext(path)[1].lower()
    if ext not in MEDIA:
        raise SystemExit("Unsupported image type (use jpg/png/webp)")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Image not found at path: {path}")
    try:
        import cv2
        import numpy as np
        with open(path, "rb") as f:
            file_bytes = np.frombuffer(f.read(), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        if img is not None:
            h, w = img.shape[:2]
            if max(h, w) > MAX_SIDE:
                k = MAX_SIDE / max(h, w)
                img = cv2.resize(img, (int(w * k), int(h * k)), interpolation=cv2.INTER_AREA)
            ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 92])
            if ok:
                return base64.standard_b64encode(buf.tobytes()).decode(), "image/jpeg"
    except Exception:
        pass
    with open(path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode(), MEDIA[ext]

def clean_and_parse_vlm_output(raw_response: str):
    cleaned_text = re.sub(r'```(?:json)?\n?|\n?```', '', raw_response or "").strip()
    start_idx = cleaned_text.find('[')
    end_idx = cleaned_text.rfind(']') + 1
    if start_idx != -1 and end_idx != -1:
        json_str = cleaned_text[start_idx:end_idx]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return []
    return []

def _parse(raw):
    parsed = clean_and_parse_vlm_output(raw)
    if parsed and isinstance(parsed, list):
        invalid_headers = {
            "quantity", "strength", "sig", "route", "refills", "refill",
            "dispense", "instructions", "date", "status", "name of the drug", "none", "n/a"
        }
        for l in parsed:
            if isinstance(l, dict):
                val = l.get("medication_name") or l.get("drug_name") or l.get("name") or l.get("text") or ""
                # Strip numbering prefixes like 'Rx 1:', 'Rx 2:', '3:', '1.', '#' completely
                val = re.sub(r'^(?:rx\s*\d*[:.-]?\s*|\d+[:.)]\s*|#\s*)', '', str(val), flags=re.IGNORECASE).strip()
                v_lower = val.lower()
                is_hdr = any(h == v_lower or v_lower.startswith(f"{h}:") or v_lower.startswith(f"{h} ") for h in invalid_headers)
                is_num = bool(re.match(r'^[\d:.\-\s#]+$', val)) or not val
                if is_hdr or is_num:
                    continue
                strn = l.get("strength")
                freq = l.get("frequency_instructions") or l.get("frequency")
                suffix = f" {strn}" if strn and strn != "-" else ""
                suffix += f" ({freq})" if freq and freq != "-" else ""
                out.append((val + suffix) + ("" if l.get("certain", True) else " [?]"))
            elif isinstance(l, str):
                out.append(l)
        if out:
            return out
    lines = [l.strip() for l in str(raw).splitlines() if l.strip()]
    if not lines:
        raise SystemExit("Model returned nothing usable - enter manually.")
    return [l + " [?]" for l in lines]

def _local_prompt():
    custom = os.environ.get("HANDWRITING_PROMPT")
    if custom: return custom.replace("\\n", "\n")
    return "Free OCR." if "ocr" in MODEL.lower() else PROMPT

def _local(path):
    if not MODEL:
        raise SystemExit("Set HANDWRITING_MODEL to an Ollama vision model you have pulled.")
        
    # CRITICAL VRAM MANAGEMENT: added "keep_alive": 0 to force model unloading & zero temperature
    body = json.dumps({
        "model": MODEL, 
        "stream": False, 
        "keep_alive": 0,
        "options": {
            "temperature": 0.0,
            "num_predict": 512
        },
        "messages": [{"role": "user", "content": _local_prompt(),
                      "images": [_b64(path)[0]]}]
    }).encode()
    
    req = urllib.request.Request(f"{OLLAMA_URL}/api/chat", body,
                                 {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read())["message"]["content"]
    except OSError as e:
        raise SystemExit(f"Could not reach Ollama at {OLLAMA_URL}: {e}")

def _api(path):
    try:
        import anthropic  # type: ignore
    except ImportError:
        raise RuntimeError("The 'anthropic' package is required when using BACKEND='api'. Run: pip install anthropic")
    data, media = _b64(path)
    msg = anthropic.Anthropic().messages.create(
        model=MODEL, max_tokens=2000,
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": media, "data": data}},
            {"type": "text", "text": PROMPT}]}])
    return "".join(b.text for b in msg.content if b.type == "text")

def transcribe(path):
    return _parse(_api(path) if BACKEND == "api" else _local(path))

# Backwards compatibility exports for existing edge-api core imports
try:
    from app.core.handwriting import (
        HandwritingVlmPipeline,
        handwriting_vlm_pipeline,
        INDIAN_PHARMACIST_VLM_PROMPT
    )
except ImportError:
    try:
        from .app.core.handwriting import (
            HandwritingVlmPipeline,
            handwriting_vlm_pipeline,
            INDIAN_PHARMACIST_VLM_PROMPT
        )
    except Exception:
        pass
