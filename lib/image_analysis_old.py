import re
from typing import Optional
import io
from PIL import Image


def parse_battle_time_to_minutes(time_text: str) -> float:
    """Parse battle time string to minutes.
    
    Supports formats like:
    - "10:10" (MM:SS)
    - "10m 10s" (with 'm' and 's' markers)
    - "600s" (seconds only)
    
    Returns: time in minutes as float
    """
    if not time_text or not isinstance(time_text, str):
        return 0.0
    
    time_text = time_text.strip()
    
    # Try MM:SS format
    if ':' in time_text:
        parts = time_text.split(':')
        try:
            minutes = int(parts[0])
            seconds = int(parts[1])
            return minutes + seconds / 60.0
        except (ValueError, IndexError):
            pass
    
    # Try "XXm YYs" format
    m_match = re.search(r'(\d+)\s*m', time_text, re.IGNORECASE)
    s_match = re.search(r'(\d+)\s*s', time_text, re.IGNORECASE)
    
    minutes = 0.0
    if m_match:
        minutes = int(m_match.group(1))
    if s_match:
        seconds = int(s_match.group(1))
        minutes += seconds / 60.0
    
    if minutes > 0:
        return minutes
    
    # Try seconds only format "XXXs"
    s_only_match = re.match(r'^(\d+)\s*s?$', time_text, re.IGNORECASE)
    if s_only_match:
        try:
            total_seconds = int(s_only_match.group(1))
            return total_seconds / 60.0
        except ValueError:
            pass
    
    return 0.0


def calculate_cpm(count: int, battle_time_minutes: float) -> float:
    """Calculate CPM (Count Per Minute).
    
    Args:
        count: Number of actions/abilities
        battle_time_minutes: Battle duration in minutes
    
    Returns: CPM as float, or 0.0 if battle_time_minutes is 0
    """
    if battle_time_minutes <= 0:
        return 0.0
    return count / battle_time_minutes


def extract_battle_time(text: str) -> Optional[str]:
    """Extract battle time from OCR text.

    Handles patterns like:
    - "전투 시간 07 : 15"
    - "전투 시간 7 : 15"
    - "07:15"
    - "07 : 15"
    Returns a zero-padded "MM:SS" string or None.
    """
    if not text:
        return None

    # Normalize whitespace and remove weird characters
    normalized = text.replace('\u200b', ' ')
    normalized = re.sub(r'\s+', ' ', normalized)

    patterns = [
        r'전투\s*시간\s*(\d{1,2})\s*[:：]\s*(\d{1,2})',
        r'(\d{1,2})\s*[:：]\s*(\d{1,2})',
    ]

    for pattern in patterns:
        match = re.search(pattern, normalized)
        if match:
            minutes = int(match.group(1))
            seconds = int(match.group(2))
            if 0 <= minutes <= 99 and 0 <= seconds < 60:
                return f"{minutes:02d}:{seconds:02d}"

    return None


def extract_back_attack_rate(text: str) -> Optional[float]:
    """Extract back attack rate percentage from OCR text.
    
    Looks for patterns like "82.60%" or "82,60%".
    Returns: percentage as float (e.g., 82.60) or None if not found
    """
    if not text:
        return None
    
    # Prefer the first percentage-like candidate from the top of the text
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    # Search line by line from top to bottom
    for line in lines:
        # Find decimal-like numbers (e.g., 82.6096, 82,60)
        dec_matches = re.findall(r'\d{1,3}[.,]\d{2,4}', line)
        if dec_matches:
            s = dec_matches[0]
            s_norm = s.replace(',', '.')
            parts = s_norm.split('.')
            integer = parts[0]
            decimal = parts[1] if len(parts) > 1 else ''
            # Truncate to two decimal places (do not round)
            if len(decimal) >= 2:
                decimal2 = decimal[:2]
            else:
                decimal2 = (decimal + '0'*2)[:2]
            try:
                return float(f"{integer}.{decimal2}")
            except ValueError:
                continue
        # If explicit percent sign exists, take that integer percent
        perc_match = re.search(r'(\d{1,3})\s*%', line)
        if perc_match:
            try:
                return float(perc_match.group(1))
            except ValueError:
                continue

    # As a fallback, search the whole text for decimal candidates and take the first
    global_dec = re.findall(r'\d{1,3}[.,]\d{2,4}', text)
    if global_dec:
        s = global_dec[0].replace(',', '.')
        parts = s.split('.')
        integer = parts[0]
        decimal = parts[1] if len(parts) > 1 else ''
        decimal2 = (decimal + '0'*2)[:2]
        try:
            return float(f"{integer}.{decimal2}")
        except ValueError:
            return None

    # No candidate found
    return None


def _get_image_bytes(image) -> bytes:
    if image is None:
        return b""

    if isinstance(image, bytes):
        return image

    if isinstance(image, io.BytesIO):
        return image.getvalue()

    if hasattr(image, 'getvalue') and callable(image.getvalue):
        try:
            return image.getvalue()
        except Exception:
            pass

    if hasattr(image, 'read') and callable(image.read):
        try:
            data = image.read()
            if hasattr(image, 'seek') and callable(image.seek):
                try:
                    image.seek(0)
                except Exception:
                    pass
            return data
        except Exception:
            pass

    if isinstance(image, Image.Image):
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        return buffer.getvalue()

    return b""


def crop_by_ratio(image, left: float, top: float, right: float, bottom: float):
    """Crop a PIL image by ratios (0..1) and return a PIL Image.

    Args:
        image: file-like object or PIL Image
        left, top, right, bottom: floats between 0 and 1
    """
    img_bytes = _get_image_bytes(image)
    if not img_bytes:
        return None

    try:
        img = Image.open(io.BytesIO(img_bytes))
    except Exception:
        return None

    w, h = img.size
    l = int(max(0, min(w, left * w)))
    t = int(max(0, min(h, top * h)))
    r = int(max(0, min(w, right * w)))
    b = int(max(0, min(h, bottom * h)))
    try:
        return img.crop((l, t, r, b))
    except Exception:
        return None


def extract_blade_burst_count(text: str) -> Optional[int]:
    """Extract blade burst usage count from OCR text.
    
    Looks for high numbers that might indicate usage count.
    Returns: count as int or None if not found
    """
    if not text:
        return None
    
    # Look for Blade Burst related keywords followed by numbers
    burst_patterns = [
        r'블레이드\s*버스트[:\s]+(\d+)',
        r'Blade\s*Burst[:\s]+(\d+)',
        r'버스트[:\s]+(\d+)',
    ]
    
    # First try patterns on single-line or inline matches
    for pattern in burst_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                val = int(match.group(1))
                if 1 <= val <= 300:
                    return val
            except ValueError:
                pass

    # Prefer searching around lines that contain '버스트' (handle OCR misreads like '불레이드')
    lines = [ln.rstrip() for ln in text.splitlines() if ln is not None]
    for i, line in enumerate(lines):
        if '버스트' in line:
            # create a window from this line to the next up to 10 lines
            window_lines = lines[i:i+11]

            # 1) Look for a whole-line integer (only digits) within the window -> highest priority
            for wl in window_lines:
                if re.match(r'^\s*\d{1,3}\s*$', wl):
                    try:
                        val = int(wl.strip())
                        if 1 <= val <= 300:
                            return val
                    except ValueError:
                        pass

            # 2) If none, collect numeric candidates not adjacent to '.' , ',' or Korean '억'
            candidates = []
            for wl in window_lines:
                # find digit tokens that are not part of decimals or suffixed with '억'
                for m in re.finditer(r'(?<![\d.,억])(\d{1,3})(?![\d.,억])', wl):
                    try:
                        num = int(m.group(1))
                        if 1 <= num <= 300:
                            candidates.append(num)
                    except ValueError:
                        continue

            # 3) From candidates, prefer those in 80-200 range; choose the last (rear) one
            wide_candidates = [c for c in candidates if 80 <= c <= 200]
            if wide_candidates:
                return wide_candidates[-1]

            # 4) If still none, if there are any candidates, return the last one
            if candidates:
                return candidates[-1]

    # If no '버스트' marker found or nothing matched, return None
    return None


def perform_ocr(image) -> dict:
    """Perform OCR on image using easyocr or pytesseract.

    Args:
        image: PIL Image, bytes, BytesIO, or file-like object

    Returns: dict with keys 'text' and 'error'
    """
    img_bytes = _get_image_bytes(image)
    if not img_bytes:
        return {"text": "", "error": "이미지 바이트를 읽을 수 없습니다."}

    error_messages = []
    text_result = ""

    try:
        import easyocr
        import numpy as np
        reader = easyocr.Reader(['ko', 'en'], gpu=False)

        pil_image = Image.open(io.BytesIO(img_bytes))
        img_array = np.array(pil_image)
        results = reader.readtext(img_array)
        text_result = '\n'.join([text[1] for text in results])
    except Exception as e:
        error_messages.append(f"easyocr failed: {e}")

    if not text_result:
        try:
            import pytesseract
            pil_image = Image.open(io.BytesIO(img_bytes))
            extracted_text = pytesseract.image_to_string(pil_image, lang='kor+eng')
            text_result = extracted_text or text_result
        except Exception as e2:
            error_messages.append(f"pytesseract failed: {e2}")

    if not text_result and error_messages:
        return {"text": "", "error": " | ".join(error_messages)}

    return {"text": text_result or "", "error": " | ".join(error_messages)}


def analyze_blade_images(summary_image, attack_image) -> dict:
    """Analyze blade-specific battle images.

    Args:
        summary_image: Uploaded summary info image
        attack_image: Uploaded attack info image

    Returns: dict with extracted metrics (battle_time, back_attack_rate, blade_burst_count)
             Fields may be None if extraction fails
    """
    result = {
        "battle_time": None,
        "back_attack_rate": None,
        "blade_burst_count": None,
        "summary_ocr_raw": "",
        "attack_ocr_raw": "",
        "ocr_error": "",
    }

    # OCR summary image - crop the back-attack card area first
    if summary_image:
        try:
            summary_ocr = perform_ocr(summary_image)
            full_summary_text = summary_ocr.get("text", "")
            summary_error = summary_ocr.get("error", "")
            result["summary_ocr_raw"] = full_summary_text or "[OCR 결과 없음]"
            if summary_error:
                result["ocr_error"] += f"summary: {summary_error}"

            # crop region likely containing back-attack rate
            cropped = crop_by_ratio(summary_image, 0.50, 0.16, 0.75, 0.31)
            cropped_text = ""
            if cropped is not None:
                cropped_ocr = perform_ocr(cropped)
                cropped_text = cropped_ocr.get("text", "")
                cropped_error = cropped_ocr.get("error", "")
                if cropped_error:
                    if result["ocr_error"]:
                        result["ocr_error"] += " | "
                    result["ocr_error"] += f"cropped: {cropped_error}"

            bar = extract_back_attack_rate(cropped_text or full_summary_text)
            if bar is not None:
                result["back_attack_rate"] = bar

            battle_time = extract_battle_time(full_summary_text)
            if battle_time:
                result["battle_time"] = battle_time
        except Exception as e:
            print(f"Error processing summary image: {e}")
            if result["ocr_error"]:
                result["ocr_error"] += " | "
            result["ocr_error"] += f"summary exception: {e}"

    # OCR attack image - try to find the '블레이드 버스트' row specifically
    if attack_image:
        try:
            attack_ocr = perform_ocr(attack_image)
            attack_text = attack_ocr.get("text", "")
            attack_error = attack_ocr.get("error", "")
            result["attack_ocr_raw"] = attack_text or "[OCR 결과 없음]"
            if attack_error:
                if result["ocr_error"]:
                    result["ocr_error"] += " | "
                result["ocr_error"] += f"attack: {attack_error}"

            blade_burst_count = extract_blade_burst_count(attack_text)
            if blade_burst_count is not None:
                result["blade_burst_count"] = blade_burst_count
        except Exception as e:
            print(f"Error processing attack image: {e}")
            if result["ocr_error"]:
                result["ocr_error"] += " | "
            result["ocr_error"] += f"attack exception: {e}"

    if not result["summary_ocr_raw"]:
        result["summary_ocr_raw"] = "[OCR 결과 없음]"
    if not result["attack_ocr_raw"]:
        result["attack_ocr_raw"] = "[OCR 결과 없음]"

    return result

def extract_breaker_nakhwa_count(text: str) -> Optional[int]:
    """
    브레이커 공격 정보 OCR 텍스트에서 '권왕십이식 : 낙화' 사용 횟수를 추출한다.
    """
    if not text:
        return None

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return None

    normalized_lines = [ln.replace(' ', '') for ln in lines]
    key_indices = [i for i, ln in enumerate(normalized_lines) if '낙화' in ln or '권왕십이식' in ln]
    if not key_indices:
        return None

    for idx in key_indices:
        window_lines = lines[idx: idx + 12]
        window_text = '\n'.join(window_lines)

        # 우선 '사용' 또는 '횟수'가 있는 줄에서 숫자를 찾는다.
        for wl in window_lines:
            if '사용' in wl or '횟수' in wl:
                candidates = re.findall(r'(?<![\d.,억%])(\d{1,3})(?![\d.,억%])', wl)
                for candidate in candidates:
                    value = int(candidate)
                    if 1 <= value <= 300:
                        return value

        # 낙화 포함 줄에서 standalone 숫자를 찾는다.
        for wl in window_lines:
            if '낙화' in wl:
                candidates = re.findall(r'(?<![\d.,억%])(\d{1,3})(?![\d.,억%])', wl)
                for candidate in candidates:
                    value = int(candidate)
                    if 1 <= value <= 300:
                        return value

        # 윈도우 전체에서 standalone 정수 후보를 찾는다.
        candidates = re.findall(r'(?<![\d.,억%])(\d{1,3})(?![\d.,억%])', window_text)
        valid = [int(c) for c in candidates if 1 <= int(c) <= 300]
        if valid:
            return valid[-1]

    return None


def extract_arcana_card_count(text: str) -> Optional[int]:
    """
    아르카나 종합 정보 OCR 텍스트에서 카드 사용 횟수를 추출한다.
    """
    if not text:
        return None

    match = re.search(r"카드\s*사용\s*횟수\s*(\d{1,4})", text)
    if match:
        return int(match.group(1))

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    for i, line in enumerate(lines):
        normalized = line.replace(" ", "")

        if "카드" in normalized and ("사용" in normalized or "횟수" in normalized):
            window_lines = lines[i:i + 5]

            for wl in window_lines:
                cleaned = wl.replace(",", "").strip()
                if re.fullmatch(r"\d{1,4}", cleaned):
                    value = int(cleaned)
                    if 1 <= value <= 999:
                        return value

    nums = re.findall(r"\b\d{2,4}\b", text)
    candidates = []
    for n in nums:
        value = int(n)
        if 50 <= value <= 500:
            candidates.append(value)

    if candidates:
        return candidates[-1]

    return None


def analyze_breaker_images(summary_image, attack_image) -> dict:
    """
    브레이커 이미지 분석.
    종합 정보 이미지에서 전투 시간, 공격 정보 이미지에서 낙화 사용 횟수를 추출한다.
    """
    result = {
        "battle_time": None,
        "nakhwa_count": None,
        "summary_ocr_raw": "",
        "attack_ocr_raw": "",
        "ocr_error": "",
    }

    if summary_image:
        try:
            summary_ocr = perform_ocr(summary_image)
            summary_text = summary_ocr.get("text", "")
            summary_error = summary_ocr.get("error", "")
            result["summary_ocr_raw"] = summary_text or "[OCR 결과 없음]"
            if summary_error:
                result["ocr_error"] += f"summary: {summary_error}"

            battle_time = extract_battle_time(summary_text)
            if battle_time:
                result["battle_time"] = battle_time
        except Exception as e:
            print(f"Error processing breaker summary image: {e}")
            result["ocr_error"] += f"summary exception: {e}"

    if attack_image:
        try:
            attack_ocr = perform_ocr(attack_image)
            attack_text = attack_ocr.get("text", "")
            attack_error = attack_ocr.get("error", "")
            result["attack_ocr_raw"] = attack_text or "[OCR 결과 없음]"
            if attack_error:
                if result["ocr_error"]:
                    result["ocr_error"] += " | "
                result["ocr_error"] += f"attack: {attack_error}"

            nakhwa_count = extract_breaker_nakhwa_count(attack_text)
            if nakhwa_count is not None:
                result["nakhwa_count"] = nakhwa_count
        except Exception as e:
            print(f"Error processing breaker attack image: {e}")
            if result["ocr_error"]:
                result["ocr_error"] += " | "
            result["ocr_error"] += f"attack exception: {e}"

    if not result["summary_ocr_raw"]:
        result["summary_ocr_raw"] = "[OCR 결과 없음]"
    if not result["attack_ocr_raw"]:
        result["attack_ocr_raw"] = "[OCR 결과 없음]"

    return result


def analyze_arcana_images(summary_image) -> dict:
    """
    아르카나 이미지 분석.
    종합 정보 이미지에서 전투 시간과 카드 사용 횟수를 추출한다.
    """
    result = {
        "battle_time": None,
        "card_count": None,
        "summary_ocr_raw": "",
        "attack_ocr_raw": "",
        "ocr_error": "",
    }

    if summary_image:
        try:
            summary_ocr = perform_ocr(summary_image)
            summary_text = summary_ocr.get("text", "")
            summary_error = summary_ocr.get("error", "")
            result["summary_ocr_raw"] = summary_text or "[OCR 결과 없음]"
            if summary_error:
                result["ocr_error"] += f"summary: {summary_error}"

            battle_time = extract_battle_time(summary_text)
            if battle_time:
                result["battle_time"] = battle_time

            card_count = extract_arcana_card_count(summary_text)
            if card_count is not None:
                result["card_count"] = card_count
        except Exception as e:
            print(f"Error processing arcana summary image: {e}")
            if result["ocr_error"]:
                result["ocr_error"] += " | "
            result["ocr_error"] += f"arcana exception: {e}"

    return result