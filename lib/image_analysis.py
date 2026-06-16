import re
from typing import Optional
import io


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
    
    # Look for MM:SS pattern
    time_pattern = r'(\d{1,2}):(\d{2})'
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
    
    # Look for percentage pattern (with . or ,)
    rate_pattern = r'(\d+)[.,](\d{2})\s*%'
    match = re.search(rate_pattern, text)
    if match:
        integer_part = match.group(1)
        decimal_part = match.group(2)
        return float(f"{integer_part}.{decimal_part}")
    
    # Look for integer percentage only
    rate_pattern_int = r'(\d{1,3})\s*%'
    match = re.search(rate_pattern_int, text)
    if match:
        return float(match.group(1))
    
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
    
    for pattern in burst_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
    
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
    
    # OCR summary image
    if summary_image:
        try:
            summary_text = perform_ocr(summary_image)
            result["summary_ocr_raw"] = summary_text
            
            # Extract battle time and back attack rate
            battle_time = extract_battle_time(summary_text)
            if battle_time:
                result["battle_time"] = battle_time
            
            back_attack_rate = extract_back_attack_rate(summary_text)
            if back_attack_rate:
                result["back_attack_rate"] = back_attack_rate
        except Exception as e:
            print(f"Error processing summary image: {e}")
    
    # OCR attack image
    if attack_image:
        try:
            attack_text = perform_ocr(attack_image)
            result["attack_ocr_raw"] = attack_text
            
            # Extract blade burst count
            blade_burst_count = extract_blade_burst_count(attack_text)
            if blade_burst_count:
                result["blade_burst_count"] = blade_burst_count
        except Exception as e:
            print(f"Error processing attack image: {e}")
    
    return result
