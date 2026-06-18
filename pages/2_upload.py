import streamlit as st
from lib.utils import render_sidebar
from lib.db_queries import load_supported_classes, load_bosses, load_score_rules, load_baselines
from lib.mock_analysis import run_mock_ocr, extract_mock_combat_metrics, create_mock_analysis_result
from lib.scoring import calculate_final_score
from lib.image_analysis import analyze_blade_images, parse_battle_time_to_minutes, calculate_cpm

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

# Blade-specific image uploads
if selected_class == "블레이드":
    st.subheader("스크린샷 업로드 (블레이드)")
    col1, col2 = st.columns(2)
    with col1:
        summary_image = st.file_uploader("종합 정보 스크린샷 (png, jpg, jpeg)", type=["png", "jpg", "jpeg"], key="summary_img")
    with col2:
        attack_image = st.file_uploader("공격 정보 스크린샷 (png, jpg, jpeg)", type=["png", "jpg", "jpeg"], key="attack_img")
else:
    # Mock upload for other classes
    uploaded_file = st.file_uploader("스크린샷 업로드 (png, jpg, jpeg)", type=["png", "jpg", "jpeg"])
    summary_image = None
    attack_image = None

video_url = st.text_input("영상 링크 (선택)")

# Initialize session state for blade analysis
if "blade_analysis_step" not in st.session_state:
    st.session_state.blade_analysis_step = None
if "blade_analysis_result" not in st.session_state:
    st.session_state.blade_analysis_result = None

# Blade analysis workflow
if selected_class == "블레이드":
    st.info("💡 블레이드 직업은 스크린샷 분석을 통해 자동으로 값이 추출됩니다. 필요시 수정 후 저장할 수 있습니다.")
    
    if st.button("분석 실행하기"):
        if not character_name:
            st.warning("캐릭터명을 입력해주세요.")
        elif not (summary_image and attack_image):
            st.warning("종합 정보와 공격 정보 스크린샷 두 장을 모두 업로드해주세요.")
        elif not selected_boss:
            st.warning("레이드를 선택해주세요.")
        else:
            st.info("이미지 분석 중입니다. 잠깐만 기다려주세요...")
            analysis_result = analyze_blade_images(summary_image, attack_image)
            st.session_state.blade_analysis_step = "review"
            st.session_state.blade_analysis_result = analysis_result
            st.rerun()
    
    # Display review UI if analysis is done
    if st.session_state.blade_analysis_step == "review":
        st.subheader("📊 추출된 값 확인 및 수정")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**종합 정보 분석 결과:**")
            battle_time_str = st.text_input(
                "전투 시간 (MM:SS 형식)",
                value=st.session_state.blade_analysis_result.get("battle_time") or "0:00",
                help="예: 10:30",
                key="battle_time_input"
            )
            back_attack_rate = st.number_input(
                "백어택 적중률 (%)",
                min_value=0.0,
                max_value=100.0,
                value=st.session_state.blade_analysis_result.get("back_attack_rate") or 0.0,
                step=0.1,
                key="back_attack_input"
            )
        
        with col2:
            st.write("**공격 정보 분석 결과:**")
            blade_burst_count = st.number_input(
                "블레이드 버스트 사용 횟수",
                min_value=0,
                value=st.session_state.blade_analysis_result.get("blade_burst_count") or 0,
                step=1,
                key="blade_burst_input"
            )
        
        # Show OCR raw text for debugging
        with st.expander("📋 OCR 원문 보기"):
            st.write("**종합 정보 OCR:**")
            st.code(st.session_state.blade_analysis_result.get("summary_ocr_raw", ""))
            st.write("**공격 정보 OCR:**")
            st.code(st.session_state.blade_analysis_result.get("attack_ocr_raw", ""))
        
        # Calculate CPM
        if battle_time_str and blade_burst_count > 0:
            battle_time_minutes = parse_battle_time_to_minutes(battle_time_str)
            if battle_time_minutes > 0:
                key_action_cpm = calculate_cpm(blade_burst_count, battle_time_minutes)
                st.success(f"✓ 블레이드 버스트 CPM: {key_action_cpm:.2f} (사용 횟수: {blade_burst_count}, 전투 시간: {battle_time_minutes:.2f}분)")
            else:
                st.warning("전투 시간을 정확히 입력해주세요.")
                key_action_cpm = 0.0
        else:
            key_action_cpm = 0.0
        
        # Store OCR raw text
        ocr_raw_text = f"Summary:\n{st.session_state.blade_analysis_result.get('summary_ocr_raw', '')}\n\nAttack:\n{st.session_state.blade_analysis_result.get('attack_ocr_raw', '')}"
        
        # Final save button
        if st.button("✅ 최종 저장"):
            if not selected_class or not selected_boss:
                st.warning("직업과 레이드를 모두 선택해주세요.")
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
                            selected_class, rules, baselines, key_action_cpm, back_attack_rate
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
                        }
                        st.session_state.blade_analysis_step = None
                        st.success("분석이 완료되었습니다. 분석 결과 화면으로 이동해주세요.")
                except Exception as e:
                    st.error(f"분석 중 오류 발생: {e}")

# Other classes (non-Blade) - mock flow
else:
    if selected_class:
        mock_metrics = extract_mock_combat_metrics(selected_class)
        key_action_cpm = st.number_input("핵심 행동 CPM", min_value=0.0, value=mock_metrics["key_action_cpm"])
        back_attack_rate = None
    else:
        key_action_cpm = 0.0
        back_attack_rate = None
    
    if st.button("분석 실행하기"):
        if not character_name:
            st.warning("캐릭터명을 입력해주세요.")
        elif not uploaded_file:
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
                        selected_class, rules, baselines, key_action_cpm, back_attack_rate
                    )
                    st.session_state["analysis_result"] = {
                        "class_name": selected_class,
                        "boss_id": boss_id,
                        "video_url": video_url,
                        "key_action_cpm": key_action_cpm,
                        "back_attack_rate": back_attack_rate,
                        "final_score": final_score,
                        "ocr_raw_text": ocr_result["ocr_raw_text"],
                        "screenshot_url": "mock://uploaded_screenshot.png",
                        "character_name": character_name,
                    }
                    st.success("분석이 완료되었습니다. 분석 결과 화면으로 이동해주세요.")
            except Exception as e:
                st.error(f"분석 중 오류 발생: {e}")
