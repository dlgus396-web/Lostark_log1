import streamlit as st

from lib.utils import render_sidebar
from lib.db_queries import load_supported_classes, load_bosses, load_score_rules, load_baselines
from lib.scoring import calculate_final_score
from lib.image_analysis import (
    analyze_blade_images,
    analyze_breaker_images,
    analyze_arcana_images,
    parse_battle_time_to_minutes,
    calculate_cpm,
)
render_sidebar()

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
character_name = st.text_input("캐릭터명", placeholder="예: 창키타카")

# 직업별 스크린샷 업로드
if selected_class in ["블레이드", "브레이커"]:
    st.subheader(f"스크린샷 업로드 ({selected_class})")
    col1, col2 = st.columns(2)

    with col1:
        summary_image = st.file_uploader(
            "종합 정보 스크린샷 (png, jpg, jpeg)",
            type=["png", "jpg", "jpeg"],
            key=f"summary_img_{selected_class}",
        )

    with col2:
        attack_image = st.file_uploader(
            "공격 정보 스크린샷 (png, jpg, jpeg)",
            type=["png", "jpg", "jpeg"],
            key=f"attack_img_{selected_class}",
        )

    uploaded_file = summary_image

elif selected_class == "아르카나":
    st.subheader("스크린샷 업로드 (아르카나)")
    summary_image = st.file_uploader(
        "종합 정보 스크린샷 (png, jpg, jpeg)",
        type=["png", "jpg", "jpeg"],
        key="summary_img_arcana",
    )
    attack_image = None
    uploaded_file = summary_image

else:
    uploaded_file = st.file_uploader(
        "스크린샷 업로드 (png, jpg, jpeg)",
        type=["png", "jpg", "jpeg"],
    )
    summary_image = None
    attack_image = None

video_url = st.text_input("영상 링크 (선택)")

# Initialize session state for blade analysis
if "analysis_step" not in st.session_state:
    st.session_state.analysis_step = None
if "ocr_analysis_result" not in st.session_state:
    st.session_state.ocr_analysis_result = None

# OCR 분석 workflow
if selected_class in ["블레이드", "브레이커", "아르카나"]:
    st.info(f"💡 {selected_class} 직업은 스크린샷 분석을 통해 값을 추출합니다. 필요시 수정 후 저장할 수 있습니다.")

    if st.button("분석 실행하기"):
        if not character_name:
            st.warning("캐릭터명을 입력해주세요.")
        elif not selected_boss:
            st.warning("레이드를 선택해주세요.")
        elif selected_class in ["블레이드", "브레이커"] and not (summary_image and attack_image):
            st.warning("종합 정보와 공격 정보 스크린샷 두 장을 모두 업로드해주세요.")
        elif selected_class == "아르카나" and not summary_image:
            st.warning("종합 정보 스크린샷을 업로드해주세요.")
        else:
            st.info("이미지 분석 중입니다. 잠깐만 기다려주세요...")

            if selected_class == "블레이드":
                analysis_result = analyze_blade_images(summary_image, attack_image)
            elif selected_class == "브레이커":
                analysis_result = analyze_breaker_images(summary_image, attack_image)
            elif selected_class == "아르카나":
                analysis_result = analyze_arcana_images(summary_image)
            else:
                analysis_result = {}

            st.session_state.analysis_step = "review"
            st.session_state.ocr_analysis_result = analysis_result
            st.rerun()

    if st.session_state.analysis_step == "review":
        st.subheader("📊 추출된 값 확인 및 수정")

        analysis = st.session_state.ocr_analysis_result or {}

        col1, col2 = st.columns(2)

        with col1:
            st.write("**종합 정보 분석 결과:**")
            battle_time_str = st.text_input(
                "전투 시간 (MM:SS 형식)",
                value=analysis.get("battle_time") or "0:00",
                help="예: 10:30",
                key="battle_time_input",
            )

            if selected_class == "블레이드":
                back_attack_rate = st.number_input(
                    "백어택 적중률 (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(analysis.get("back_attack_rate") or 0.0),
                    step=0.1,
                    key="back_attack_input",
                )
            else:
                back_attack_rate = None

        with col2:
            st.write("**핵심 행동 분석 결과:**")

            if selected_class == "블레이드":
                key_action_name = "블레이드 버스트"
                default_count = analysis.get("blade_burst_count") or 0
                count_label = "블레이드 버스트 사용 횟수"

            elif selected_class == "브레이커":
                key_action_name = "권왕십이식 : 낙화"
                default_count = analysis.get("nakhwa_count") or 0
                count_label = "권왕십이식 : 낙화 사용 횟수"

            elif selected_class == "아르카나":
                key_action_name = "카드 사용"
                default_count = analysis.get("card_count") or 0
                count_label = "카드 사용 횟수"

            else:
                key_action_name = "핵심 행동"
                default_count = 0
                count_label = "핵심 행동 사용 횟수"

            key_action_count = st.number_input(
                count_label,
                min_value=0,
                value=int(default_count),
                step=1,
                key="key_action_count_input",
            )

        with st.expander("📋 OCR 원문 보기"):
            st.write("**종합 정보 OCR:**")
            st.code(analysis.get("summary_ocr_raw", ""))
            if selected_class in ["블레이드", "브레이커"]:
                st.write("**공격 정보 OCR:**")
                st.code(analysis.get("attack_ocr_raw", ""))

        if battle_time_str and key_action_count > 0:
            battle_time_minutes = parse_battle_time_to_minutes(battle_time_str)
            if battle_time_minutes > 0:
                key_action_cpm = calculate_cpm(key_action_count, battle_time_minutes)
                st.success(
                    f"✓ {key_action_name} CPM: {key_action_cpm:.2f} "
                    f"(사용 횟수: {key_action_count}, 전투 시간: {battle_time_minutes:.2f}분)"
                )
            else:
                st.warning("전투 시간을 정확히 입력해주세요.")
                key_action_cpm = 0.0
        else:
            battle_time_minutes = 0.0
            key_action_cpm = 0.0

        ocr_raw_text = (
            f"Summary:\n{analysis.get('summary_ocr_raw', '')}\n\n"
            f"Attack:\n{analysis.get('attack_ocr_raw', '')}"
        )

        if st.button("✅ 최종 저장"):
            if not selected_class or not selected_boss:
                st.warning("직업과 레이드를 모두 선택해주세요.")
            elif key_action_cpm <= 0:
                st.warning("핵심 행동 CPM이 0입니다. 전투 시간과 사용 횟수를 확인해주세요.")
            else:
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
                            selected_class,
                            rules,
                            baselines,
                            key_action_cpm,
                            back_attack_rate,
                        )

                        st.session_state["analysis_result"] = {
                            "class_name": selected_class,
                            "boss_id": boss_id,
                            "video_url": video_url,
                            "key_action_cpm": key_action_cpm,
                            "back_attack_rate": back_attack_rate,
                            "final_score": final_score,
                            "ocr_raw_text": ocr_raw_text,
                            "screenshot_url": "mock://uploaded_screenshot.png",
                            "character_name": character_name,
                            "key_action_name": key_action_name,
                            "key_action_count": key_action_count,
                            "battle_time_text": battle_time_str,
                            "battle_time_minutes": battle_time_minutes,
                            "ocr_status": "success",
                        }

                        st.session_state.analysis_step = None
                        st.success("분석이 완료되었습니다. 분석 결과 화면으로 이동해주세요.")

                except Exception as e:
                    st.error(f"분석 중 오류 발생: {e}")

else:
    st.info("선택한 직업에 대한 분석 기능이 아직 준비되지 않았습니다.")

