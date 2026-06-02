def run_mock_ocr(uploaded_file):
    return {
        "ocr_status": "mock_success",
        "ocr_raw_text": "기본틀 mock OCR 결과입니다. 실제 OCR은 추후 구현합니다."
    }

def mock_upload_screenshot(uploaded_file):
    if uploaded_file is None:
        return None
    return "mock://uploaded_screenshot.png"

def extract_mock_combat_metrics(selected_class: str):
    if selected_class == "블레이드":
        return {
            "key_action_cpm": 6.0,
            "back_attack_rate": 75.0,
            "head_attack_rate": None
        }
    if selected_class == "브레이커":
        return {
            "key_action_cpm": 3.2,
            "back_attack_rate": None,
            "head_attack_rate": 80.0
        }
    if selected_class == "아르카나":
        return {
            "key_action_cpm": 22.0,
            "back_attack_rate": None,
            "head_attack_rate": None
        }
    return {
        "key_action_cpm": 0.0,
        "back_attack_rate": None,
        "head_attack_rate": None
    }

def create_mock_analysis_result(selected_class: str, selected_boss_id: int, video_url: str | None):
    metrics = extract_mock_combat_metrics(selected_class)
    return {
        "class_name": selected_class,
        "boss_id": selected_boss_id,
        "video_url": video_url,
        **metrics
    }

def mock_save_combat_record(record: dict):
    return {
        "success": True,
        "message": "기본틀에서는 실제 DB 저장 없이 mock 저장 처리되었습니다."
    }
