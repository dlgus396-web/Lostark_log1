import re
import time
from datetime import datetime
from lib.supabase_client import get_supabase_client


BUCKET_NAME = "combat-screenshots"


def _safe_filename(original: str) -> str:
    # replace spaces with underscore
    name = original.replace(" ", "_")
    # remove path separators
    name = name.replace("/", "_").replace("\\\\", "_")
    # allow alphanum, ., -, _, and Korean chars
    name = re.sub(r"[^0-9A-Za-z가-힣._-]", "", name)
    if not name:
        # fallback name with timestamp
        name = f"file_{int(time.time())}.bin"
    return name


def _extract_ext(filename: str) -> str:
    parts = filename.rsplit(".", 1)
    if len(parts) == 2 and parts[1]:
        return parts[1]
    return "bin"


def upload_combat_screenshot(uploaded_file, user_id: str, label: str = "summary") -> str:
    """Upload a Streamlit uploaded file to Supabase Storage and return public URL.

    Path format: user_id/yyyyMMdd_HHmmss_label_originalfilename

    Raises an exception on failure.
    """
    if not uploaded_file:
        raise ValueError("uploaded_file is required")
    if not user_id:
        raise ValueError("user_id is required")

    supabase = get_supabase_client()

    original_name = getattr(uploaded_file, "name", None) or "upload"
    # preserve extension
    ext = _extract_ext(original_name)
    base = original_name.rsplit(".", 1)[0] if "." in original_name else original_name
    # sanitize base name
    base_safe = _safe_filename(base)
    if not base_safe:
        base_safe = f"file_{int(time.time())}"

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    label_safe = _safe_filename(label)
    filename = f"{timestamp}_{label_safe}_{base_safe}.{ext}"
    path = f"{user_id}/{filename}"

    # read bytes (use getvalue as requested)
    try:
        file_bytes = uploaded_file.getvalue()
    except Exception:
        try:
            file_bytes = uploaded_file.read()
        except Exception:
            file_bytes = None

    if file_bytes is None:
        raise RuntimeError("파일을 읽을 수 없습니다.")

    content_type = getattr(uploaded_file, "type", None) or "image/png"

    bucket = supabase.storage.from_(BUCKET_NAME)

    # Try common upload signatures with upsert and content type
    upload_err = None
    try:
        # Preferred: upload(path, file, content_type=..., upsert=True)
        res = bucket.upload(path, file_bytes, content_type=content_type, upsert=True)
    except TypeError:
        try:
            # Alternate: upload(path, file, {'content-type': content_type}, upsert=True)
            res = bucket.upload(path, file_bytes, {"content-type": content_type}, upsert=True)
        except Exception as e:
            upload_err = e
            res = None
    except Exception as e:
        upload_err = e
        res = None

    if upload_err or (isinstance(res, dict) and res.get("error")):
        raise RuntimeError(f"Storage upload error: {upload_err or res.get('error')}")

    # get public url
    pub = bucket.get_public_url(path)
    url = None
    if isinstance(pub, dict):
        url = pub.get("publicUrl") or pub.get("public_url") or (pub.get("data") and pub["data"].get("publicUrl"))
    elif isinstance(pub, str):
        url = pub
    else:
        url = getattr(pub, "public_url", None) or getattr(pub, "publicUrl", None)

    if not url:
        try:
            sb_url = supabase.client_url
            url = f"{sb_url}/storage/v1/object/public/{BUCKET_NAME}/{path}"
        except Exception:
            raise RuntimeError("공개 URL을 생성할 수 없습니다.")

    return url
