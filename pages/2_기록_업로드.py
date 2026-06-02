import streamlit as st
from lib.db_queries import load_supported_classes, load_bosses, load_score_rules, load_baselines
from lib.mock_analysis import run_mock_ocr, extract_mock_combat_metrics, create_mock_analysis_result
from lib.scoring import calculate_final_score

st.title("전투 기록 업로드")

try:
    classes = load_supported_classes()
except Exception as e:
    st.error("지원 직업 데이터를 불러오지 못했습니다.")
    st.caption(str(e))
    classes = []

try:
    bosses = load_bosses()
except Exception as e:
    st.error("레이드 데이터를 불러오지 못했습니다.")
    st.caption(str(e))
    bosses = []

if not classes:
    st.warning("supported_classes 데이터가 없습니다. Supabase seed 데이터를 확인해주세요.")
if not bosses:
    st.warning("bosses 데이터가 없습니다. Supabase seed 데이터를 확인해주세요.")

class_names = [c["class_name"] for c in classes] if classes else []
boss_names = [b["boss_display_name"] for b in bosses] if bosses else []

selected_class = st.selectbox("직업 선택", class_names) if class_names else None
selected_boss = st.selectbox("레이드 선택", boss_names) if boss_names else None

uploaded_file = st.file_uploader("스크린샷 업로드 (png, jpg, jpeg)", type=["png", "jpg", "jpeg"])
video_url = st.text_input("영상 링크 (선택)")

mock_metrics = {}
if selected_class:
    mock_metrics = extract_mock_combat_metrics(selected_class)
    key_action_cpm = st.number_input("핵심 행동 CPM", min_value=0.0, value=mock_metrics["key_action_cpm"])
    back_attack_rate = None
    head_attack_rate = None
    if selected_class == "블레이드":
        back_attack_rate = st.number_input("백어택 적중률", min_value=0.0, max_value=100.0, value=mock_metrics["back_attack_rate"] or 0.0)
    if selected_class == "브레이커":
        head_attack_rate = st.number_input("헤드어택 적중률", min_value=0.0, max_value=100.0, value=mock_metrics["head_attack_rate"] or 0.0)
else:
    key_action_cpm = 0.0
    back_attack_rate = None
    head_attack_rate = None

if st.button("분석 실행하기"):
    if not uploaded_file:
        st.warning("분석할 스크린샷 파일을 업로드해주세요.")
    elif not selected_class or not selected_boss:
        st.warning("직업과 레이드를 모두 선택해주세요.")
    else:
        ocr_result = run_mock_ocr(uploaded_file)
        boss_id = next((b["id"] for b in bosses if b["boss_display_name"] == selected_boss), None)
        try:
            rules = load_score_rules(selected_class)
            baselines = load_baselines(selected_class, boss_id)
            if not rules:
                st.warning("선택한 직업의 score_rules 데이터가 없습니다.")
            elif not baselines:
                st.warning("선택한 직업/레이드에 해당하는 scoring_baselines 데이터가 없습니다.")
            else:
                final_score = calculate_final_score(
                    selected_class, rules, baselines, key_action_cpm, back_attack_rate, head_attack_rate
                )
                st.session_state["analysis_result"] = {
                    "class_name": selected_class,
                    "boss_id": boss_id,
                    "video_url": video_url,
                    "key_action_cpm": key_action_cpm,
                    "back_attack_rate": back_attack_rate,
                    "head_attack_rate": head_attack_rate,
                    "final_score": final_score,
                    "ocr_raw_text": ocr_result["ocr_raw_text"],
                    "screenshot_url": "mock://uploaded_screenshot.png"
                }
                st.success("분석이 완료되었습니다. 분석 결과 화면으로 이동해주세요.")
        except Exception as e:
            st.error(f"분석 중 오류 발생: {e}")
