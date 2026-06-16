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
    
    Looks for patterns like "10:10" (MM:SS) or "10m 10s".
    Returns: time string like "10:10" or None if not found
    """
    if not text:
        return None
    
    # Look for MM:SS pattern (allow spaces around colon)
    time_pattern = r'(\d{1,2})\s*:\s*(\d{2})'
    match = re.search(time_pattern, text)
    if match:
        return f"{match.group(1)}:{match.group(2)}"
    
    # Look for XXm YYs pattern
    time_pattern_m = r'(\d{1,2})\s*m(?:in)?\s+(\d{1,2})\s*s(?:ec)?'
    match = re.search(time_pattern_m, text, re.IGNORECASE)
    if match:
        return f"{match.group(1)}:{match.group(2)}"
    
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


def crop_by_ratio(image, left: float, top: float, right: float, bottom: float):
    """Crop a PIL image by ratios (0..1) and return a PIL Image.

    Args:
        image: file-like object or PIL Image
        left, top, right, bottom: floats between 0 and 1
    """
    # Ensure we have a PIL Image
    if hasattr(image, 'read'):
        img = Image.open(image)
    elif isinstance(image, Image.Image):
        img = image
    else:
        try:
            img = Image.open(io.BytesIO(image))
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


def perform_ocr(image) -> str:
    """Perform OCR on image using easyocr or pytesseract.
    
    Args:
        image: PIL Image or file-like object
    
    Returns: OCR extracted text as string, or empty string if OCR fails
    """
    try:
        import easyocr
        reader = easyocr.Reader(['ko', 'en'], gpu=False)
        
        # Convert PIL image to bytes if needed
        if hasattr(image, 'read'):
            img_bytes = image.read()
        else:
            # PIL Image
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            img_bytes = img_bytes.getvalue()
        
        # Read image from bytes
        import numpy as np
        from PIL import Image
        pil_image = Image.open(io.BytesIO(img_bytes))
        img_array = np.array(pil_image)
        
        results = reader.readtext(img_array)
        extracted_text = '\n'.join([text[1] for text in results])
        return extracted_text
    except Exception as e:
        print(f"easyocr failed: {e}")
        try:
            import pytesseract
            from PIL import Image
            
            if hasattr(image, 'read'):
                pil_image = Image.open(image)
            else:
                pil_image = image
            
            extracted_text = pytesseract.image_to_string(pil_image, lang='kor+eng')
            return extracted_text
        except Exception as e2:
            print(f"pytesseract also failed: {e2}")
            return ""


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
    }
    
    # OCR summary image - crop the back-attack card area first
    if summary_image:
        try:
            # full summary OCR for debugging
            try:
                full_summary_text = perform_ocr(summary_image)
            except Exception:
                full_summary_text = ""
            result["summary_ocr_raw"] = full_summary_text

            # crop region likely containing back-attack rate
            cropped = crop_by_ratio(summary_image, 0.50, 0.16, 0.75, 0.31)
            cropped_text = ""
            if cropped is not None:
                try:
                    cropped_text = perform_ocr(cropped)
                except Exception:
                    cropped_text = ""
            # prefer cropped_text for extracting back attack rate
            bar = extract_back_attack_rate(cropped_text or full_summary_text)
            if bar is not None:
                result["back_attack_rate"] = bar

            battle_time = extract_battle_time(full_summary_text)
            if battle_time:
                result["battle_time"] = battle_time
        except Exception as e:
            print(f"Error processing summary image: {e}")
    
    # OCR attack image - try to find the '블레이드 버스트' row specifically
    if attack_image:
        try:
            attack_text = perform_ocr(attack_image)
            result["attack_ocr_raw"] = attack_text

            blade_burst_count = extract_blade_burst_count(attack_text)
            if blade_burst_count is not None:
                result["blade_burst_count"] = blade_burst_count
        except Exception as e:
            print(f"Error processing attack image: {e}")
    
    return result
