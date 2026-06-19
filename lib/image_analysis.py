import re
from typing import Optional
import io
from PIL import Image


def parse_battle_time_to_minutes(time_text: str) -> float:
    if not time_text or not isinstance(time_text, str):
        return 0.0
    
    time_text = time_text.strip()
    if ':' in time_text:
        parts = time_text.split(':')
        try:
            minutes = int(parts[0])
            seconds = int(parts[1])
            return minutes + seconds / 60.0
        except (ValueError, IndexError):
            pass
    
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
    
    s_only_match = re.match(r'^(\d+)\s*s?$', time_text, re.IGNORECASE)
    if s_only_match:
        try:
            total_seconds = int(s_only_match.group(1))
            return total_seconds / 60.0
        except ValueError:
            pass
    
    return 0.0


def calculate_cpm(count: int, battle_time_minutes: float) -> float:
    if battle_time_minutes <= 0:
        return 0.0
    return count / battle_time_minutes


def extract_battle_time(text: str) -> Optional[str]:
    if not text:
        return None
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
    if not text:
        return None
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for line in lines:
        dec_matches = re.findall(r'\d{1,3}[.,]\d{2,4}', line)
        if dec_matches:
            s = dec_matches[0]
            s_norm = s.replace(',', '.')
            parts = s_norm.split('.')
            integer = parts[0]
            decimal = parts[1] if len(parts) > 1 else ''
            if len(decimal) >= 2:
                decimal2 = decimal[:2]
            else:
                decimal2 = (decimal + '0'*2)[:2]
            try:
                return float(f"{integer}.{decimal2}")
            except ValueError:
                continue
        perc_match = re.search(r'(\d{1,3})\s*%', line)
        if perc_match:
            try:
                return float(perc_match.group(1))
            except ValueError:
                continue
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
    if not text:
        return None
    normalized = text.replace('\u200b', ' ').replace('\xa0', ' ')
    normalized = re.sub(r'\r\n|\r', '\n', normalized)
    lines = [ln.strip() for ln in normalized.splitlines() if ln.strip()]

    burst_patterns = [
        r'(?:블레이드|불레이드)\s*버스트[:\s]+(\d+)',
        r'Blade\s*Burst[:\s]+(\d+)',
        r'버스트[:\s]+(\d+)',
    ]
    for pattern in burst_patterns:
        for line in lines:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                try:
                    val = int(match.group(1))
                    if 1 <= val <= 300:
                        return val
                except ValueError:
                    pass

    for i, line in enumerate(lines):
        if re.search(r'(?:블레이드|불레이드).*버스트', line, re.IGNORECASE) or '버스트' in line:
            for wl in lines[i + 1 : i + 10]:
                cleaned = wl.replace(',', '').strip()
                if re.fullmatch(r'\d{1,3}', cleaned):
                    try:
                        val = int(cleaned)
                        if 1 <= val <= 300:
                            return val
                    except ValueError:
                        pass
            candidates = []
            for wl in lines[i + 1 : i + 10]:
                if '.' in wl or ',' in wl:
                    continue
                for m in re.finditer(r'(?<![\d억만%])([0-9]{1,3})(?![\d억만%])', wl):
                    try:
                        num = int(m.group(1))
                        if 1 <= num <= 300:
                            candidates.append(num)
                    except ValueError:
                        continue
            if candidates:
                return candidates[-1]
    return None


def perform_ocr(image) -> dict:
    img_bytes = _get_image_bytes(image)
    if not img_bytes:
        return {"text": "", "error": "Cannot read image bytes"}
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
    result = {
        "battle_time": None,
        "back_attack_rate": None,
        "blade_burst_count": None,
        "summary_ocr_raw": "",
        "attack_ocr_raw": "",
        "ocr_error": "",
    }
    if summary_image:
        try:
            summary_ocr = perform_ocr(summary_image)
            full_summary_text = summary_ocr.get("text", "")
            summary_error = summary_ocr.get("error", "")
            result["summary_ocr_raw"] = full_summary_text or "[OCR 결과 없음]"
            if summary_error:
                result["ocr_error"] += f"summary: {summary_error}"
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


def _extract_clean_integers(text: str) -> list:
    if not text:
        return []
    text_norm = re.sub(r'\d+\.\d+', '', text)
    text_norm = re.sub(r'\d+억', '', text_norm)
    text_norm = re.sub(r'\d+%', '', text_norm)
    candidates = re.findall(r'(?<!\d)(\d{1,3})(?!\d)', text_norm)
    return candidates


def extract_breaker_nakhwa_count(text: str) -> Optional[int]:
    if not text:
        return None
    normalized = text.replace('\u200b', ' ').replace('\xa0', ' ')
    normalized = re.sub(r'[.,]{1,2}', ' ', normalized)
    normalized = re.sub(r'\s+', ' ', normalized)
    lines = [ln.strip() for ln in normalized.splitlines() if ln.strip()]
    if not lines:
        return None

    def extract_simple_numbers(source: str) -> list[int]:
        return [int(m.group(1)) for m in re.finditer(r'(?<![\d억만%])([0-9]{1,3})(?![\d억만%])', source)]

    direct_patterns = [
        r'(?:권왕십이식|낙화)[^\d\n]{0,50}([0-9]{1,3})',
        r'낙화\s*[:：]?\s*([0-9]{1,3})',
        r'권왕십이식\s*[:：]?\s*낙화[^\d\n]{0,50}([0-9]{1,3})',
        r'낙화[^\d\n]{0,30}사용[^\d\n]{0,30}([0-9]{1,3})',
        r'사용\s*횟수[^\d\n]{0,30}([0-9]{1,3})',
        r'([0-9]{1,3})\s*회',
    ]
    for pattern in direct_patterns:
        for match in re.finditer(pattern, normalized):
            try:
                value = int(match.group(1))
                if 1 <= value <= 300:
                    return value
            except (ValueError, IndexError):
                continue

    normalized_lines = [ln.replace(' ', '') for ln in lines]
    key_indices = [i for i, ln in enumerate(normalized_lines) if '낙화' in ln or '권왕십이식' in ln]
    if not key_indices:
        return None

    for idx in key_indices:
        window_lines = lines[idx: idx + 18]
        window_text = ' '.join(window_lines)

        for wl in window_lines:
            if any(keyword in wl for keyword in ['사용', '횟수', '회']):
                candidates = extract_simple_numbers(wl)
                for v in candidates:
                    if 1 <= v <= 300:
                        return v

        for line in window_lines:
            if '낙화' in line or '권왕십이식' in line:
                candidates = extract_simple_numbers(line)
                for v in candidates:
                    if 1 <= v <= 300:
                        return v

        nearby_candidates = extract_simple_numbers(window_text)
        filtered = [v for v in nearby_candidates if 1 <= v <= 300]
        if filtered:
            return filtered[-1]

    # last fallback: try image crop-based extraction if text-based extraction fails
    return None


def extract_breaker_nakhwa_count_from_image(attack_image) -> Optional[int]:
    if not attack_image:
        return None
    crop_regions = [(0.76, 0.24, 0.90, 0.33), (0.72, 0.22, 0.90, 0.36), (0.78, 0.20, 0.88, 0.31)]
    for left, top, right, bottom in crop_regions:
        cropped = crop_by_ratio(attack_image, left, top, right, bottom)
        if cropped is None:
            continue
        try:
            crop_ocr = perform_ocr(cropped)
            crop_text = crop_ocr.get("text", "")
            if not crop_text:
                continue
            candidates = _extract_clean_integers(crop_text)
            for c in candidates:
                v = int(c)
                if 20 <= v <= 300:
                    return v
        except Exception as e:
            print(f"Crop error ({left},{top},{right},{bottom}): {e}")
            continue
    return None


def extract_arcana_card_count(text: str) -> Optional[int]:
    if not text:
        return None

    # Prefer explicit label '카드 사용 횟수' followed by a nearby integer in 50..500
    normalized = text.replace('\u200b', ' ')
    m = re.search(r'카드\s*사용\s*횟수\s*(\d{1,4})', normalized)
    if m:
        try:
            val = int(m.group(1))
            if 50 <= val <= 500:
                return val
        except ValueError:
            pass

    # Search lines where 카드/사용/횟수가 가까이 있는 경우 (window 5 lines)
    lines = [ln.strip() for ln in normalized.splitlines() if ln.strip()]
    for i, line in enumerate(lines):
        condensed = line.replace(' ', '')
        if '카드' in condensed and ('사용' in condensed or '횟수' in condensed):
            window_start = max(0, i - 2)
            window_lines = lines[window_start: i + 3]
            # collect integer candidates excluding decimals and large/small noise
            candidates = []
            for wl in window_lines:
                for c in _extract_clean_integers(wl):
                    try:
                        v = int(c)
                        if 50 <= v <= 500:
                            candidates.append(v)
                    except ValueError:
                        continue
            if candidates:
                return candidates[-1]

    # As a fallback, scan whole text for integers in 50..500
    nums = re.findall(r"\b(\d{2,4})\b", normalized)
    candidates = [int(n) for n in nums if 50 <= int(n) <= 500]
    if candidates:
        return candidates[-1]

    return None


def extract_arcana_card_count_from_image(summary_image) -> tuple[Optional[int], str]:
    """Crop top-right card area(s) and OCR to find card usage count.

    Returns: (value or None, crop_ocr_raw_text)
    """
    if not summary_image:
        return None, ""

    crop_regions = [
        (0.74, 0.16, 0.99, 0.34),
        (0.70, 0.13, 0.99, 0.36),
        (0.76, 0.18, 0.98, 0.32),
    ]

    collected_texts = []
    for left, top, right, bottom in crop_regions:
        cropped = crop_by_ratio(summary_image, left, top, right, bottom)
        if cropped is None:
            continue
        try:
            crop_ocr = perform_ocr(cropped)
            crop_text = crop_ocr.get("text", "")
            collected_texts.append(crop_text)
            if not crop_text:
                continue
            # find integers in crop_text
            for c in _extract_clean_integers(crop_text):
                try:
                    v = int(c)
                    if 50 <= v <= 500:
                        # return first valid
                        return v, "\n\n".join(collected_texts)
                except ValueError:
                    continue
        except Exception as e:
            collected_texts.append(f"[crop error: {e}]")
            continue

    return None, "\n\n".join(collected_texts)


def analyze_breaker_images(summary_image, attack_image) -> dict:
    result = {
        "battle_time": None,
        "nakhwa_count": None,
        "summary_ocr_raw": "",
        "attack_ocr_raw": "",
        "attack_crop_ocr_raw": "",
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
            if nakhwa_count is None or nakhwa_count < 15 or nakhwa_count > 80:
                try:
                    crop_nakhwa = extract_breaker_nakhwa_count_from_image(attack_image)
                    if crop_nakhwa is not None:
                        result["attack_crop_ocr_raw"] = f"[Crop OCR result: {crop_nakhwa}]"
                        nakhwa_count = crop_nakhwa
                    else:
                        result["attack_crop_ocr_raw"] = "[Crop OCR: No result or fallback value]"
                except Exception as crop_error:
                    print(f"Error in crop extraction: {crop_error}")
                    result["attack_crop_ocr_raw"] = f"[Crop OCR error: {crop_error}]"
            else:
                result["attack_crop_ocr_raw"] = "[Crop skip: valid text result found]"
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
    if not result["attack_crop_ocr_raw"]:
        result["attack_crop_ocr_raw"] = ""
    return result


def analyze_arcana_images(summary_image) -> dict:
    result = {
        "battle_time": None,
        "card_count": None,
        "summary_ocr_raw": "",
        "card_crop_ocr_raw": "",
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
            # 텍스트 기반 추출 우선
            card_count = extract_arcana_card_count(summary_text)
            # 텍스트 기반 결과가 없거나 50 미만이면 crop 기반 추출 시도
            if card_count is None or card_count < 50:
                try:
                    crop_val, crop_text = extract_arcana_card_count_from_image(summary_image)
                    result["card_crop_ocr_raw"] = crop_text or ""
                    if crop_val is not None:
                        result["card_count"] = crop_val
                    else:
                        # if crop also fails, preserve any text-based if it's >=50
                        if card_count is not None and card_count >= 50:
                            result["card_count"] = card_count
                        else:
                            result["card_count"] = None
                except Exception as e:
                    result["ocr_error"] += f" | crop exception: {e}"
                    if card_count is not None and card_count >= 50:
                        result["card_count"] = card_count
                    else:
                        result["card_count"] = None
            else:
                result["card_count"] = card_count
        except Exception as e:
            print(f"Error processing arcana summary image: {e}")
            if result["ocr_error"]:
                result["ocr_error"] += " | "
            result["ocr_error"] += f"arcana exception: {e}"
    return result
