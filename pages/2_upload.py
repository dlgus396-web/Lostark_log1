import streamlit as st
from lib.utils import render_sidebar
from lib.db_queries import load_supported_classes, load_bosses, load_score_rules, load_baselines
from lib.mock_analysis import run_mock_ocr, extract_mock_combat_metrics
from lib.scoring import calculate_final_score
from lib.storage import upload_combat_screenshot
from lib.image_analysis import (
    analyze_images_by_class,
    parse_battle_time_to_minutes,
    calculate_cpm,
)

render_sidebar()

user = st.session_state.get("user")
if not user:
    st.warning("로그인 후 기록 업로드를 이용할 수 있습니다. 로그인 페이지에서 이메일/비밀번호로 로그인해주세요.")
    st.stop()

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
selected_boss = st.selectbox("레이드 선택", boss_names) if bosses else None

supported_auto_classes = ["블레이드", "브레이커", "아르카나"]
action_label_map = {
    "블레이드": "블레이드 버스트 사용 횟수",
    "브레이커": "권왕십이식 : 낙화 사용 횟수",
    "아르카나": "카드 사용 횟수",
}
count_field_map = {
    "블레이드": "blade_burst_count",
    "브레이커": "breaker_nakhwa_count",
    "아르카나": "arcana_card_count",
}
key_action_name_map = {
    "블레이드": "블레이드 버스트",
    "브레이커": "권왕십이식 : 낙화",
    "아르카나": "카드 사용",
}

summary_image = None
attack_image = None
uploaded_file = None

if selected_class in supported_auto_classes:
    st.subheader(f"스크린샷 업로드 ({selected_class})")
    col1, col2 = st.columns(2)
    with col1:
        summary_image = st.file_uploader(
            "종합 정보 스크린샷 (png, jpg, jpeg)",
            type=["png", "jpg", "jpeg"],
            key="summary_img",
        )
    with col2:
        if selected_class == "아르카나":
            attack_image = st.file_uploader(
                "공격 정보 스크린샷 (선택)",
                type=["png", "jpg", "jpeg"],
                key="attack_img",
                help="카드 사용 횟수가 종합 정보 이미지에서 추출되지 않을 경우 보조로 업로드하세요.",
            )
        else:
            attack_image = st.file_uploader(
                "공격 정보 스크린샷 (png, jpg, jpeg)",
                type=["png", "jpg", "jpeg"],
                key="attack_img",
            )
else:
    uploaded_file = st.file_uploader("스크린샷 업로드 (png, jpg, jpeg)", type=["png", "jpg", "jpeg"])

video_url = st.text_input("영상 링크 (선택)")

if "analysis_step" not in st.session_state:
    st.session_state.analysis_step = None
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

if selected_class in supported_auto_classes:
    st.info("💡 스크린샷 분석을 통해 핵심 횟수를 추출합니다. OCR이 실패하면 직접 입력하실 수 있습니다.")

    if st.button("분석 실행하기"):
        if not summary_image:
            st.warning("종합 정보 스크린샷을 업로드해주세요.")
        elif selected_class in ["블레이드", "브레이커"] and not attack_image:
            st.warning("공격 정보 스크린샷을 업로드해주세요.")
        elif not selected_boss:
            st.warning("레이드를 선택해주세요.")
        else:
            st.info("이미지 분석 중입니다. 잠깐만 기다려주세요...")
            try:
                raw_result = analyze_images_by_class(selected_class, summary_image, attack_image)
                # upload screenshots to Supabase Storage (non-blocking on failure)
                summary_url = "mock://uploaded_screenshot.png"
                attack_url = None
                try:
                    summary_url = upload_combat_screenshot(summary_image, user["id"], label="summary")
                except Exception as e:
                    st.error("스크린샷 업로드 중 오류가 발생했습니다.")
                    st.caption(str(e))
                    summary_url = "mock://uploaded_screenshot.png"
                if attack_image:
                    try:
                        attack_url = upload_combat_screenshot(attack_image, user["id"], label="attack")
                    except Exception as e:
                        st.error("스크린샷 업로드 중 오류가 발생했습니다.")
                        st.caption(str(e))
                        attack_url = None
                ocr_text = f"Summary:\n{raw_result.get('summary_ocr_raw', '')}\n\nAttack:\n{raw_result.get('attack_ocr_raw', '')}"
                extracted_count = raw_result.get(count_field_map[selected_class]) or 0
                extracted_battle_time = raw_result.get("battle_time") or ""
                extracted_battle_minutes = (
                    parse_battle_time_to_minutes(extracted_battle_time)
                    if extracted_battle_time
                    else 0.0
                )
                key_action_cpm = calculate_cpm(extracted_count, extracted_battle_minutes) if extracted_battle_minutes > 0 else 0.0
                ocr_status = "ocr_success" if raw_result.get("summary_ocr_raw") or raw_result.get("attack_ocr_raw") else "ocr_failed"
                analysis_result = {
                    "class_name": selected_class,
                    "boss_id": next((b["id"] for b in bosses if b["boss_display_name"] == selected_boss), None),
                    "boss_name_raw": selected_boss,
                    "battle_time_text": extracted_battle_time,
                    "battle_time_minutes": extracted_battle_minutes,
                    "key_action_name": key_action_name_map[selected_class],
                    "key_action_count": extracted_count,
                    "key_action_cpm": key_action_cpm,
                    "back_attack_rate": raw_result.get("back_attack_rate"),
                    "head_attack_rate": None,
                    "final_score": 0.0,
                    "score_version": "v1",
                    "video_url": video_url,
                    "screenshot_url": summary_url,
                    "ocr_raw_text": ocr_text,
                    "ocr_status": ocr_status,
                    "summary_ocr_raw": raw_result.get("summary_ocr_raw", ""),
                    "attack_ocr_raw": raw_result.get("attack_ocr_raw", ""),
                    "attack_screenshot_url": attack_url,
                }
            except Exception:
                st.error("이미지 분석 중 오류가 발생했습니다. 직접 입력해주세요.")
                analysis_result = {
                    "class_name": selected_class,
                    "boss_id": next((b["id"] for b in bosses if b["boss_display_name"] == selected_boss), None),
                    "boss_name_raw": selected_boss,
                    "battle_time_text": "",
                    "battle_time_minutes": 0.0,
                    "key_action_name": key_action_name_map[selected_class],
                    "key_action_count": 0,
                    "key_action_cpm": 0.0,
                    "back_attack_rate": None,
                    "head_attack_rate": None,
                    "final_score": 0.0,
                    "score_version": "v1",
                    "video_url": video_url,
                    "screenshot_url": "mock://uploaded_screenshot.png",
                    "ocr_raw_text": "",
                    "ocr_status": "ocr_failed",
                    "summary_ocr_raw": "",
                    "attack_ocr_raw": "",
                }
            st.session_state.analysis_step = "review"
            st.session_state.analysis_result = analysis_result
            st.rerun()

    if st.session_state.analysis_step == "review" and st.session_state.analysis_result:
        st.subheader("📊 추출된 값 확인 및 수정")
        col1, col2 = st.columns(2)

        with col1:
            st.write("**종합 정보 분석 결과:**")
            battle_time_str = st.text_input(
                "전투 시간 (MM:SS 형식)",
                value=st.session_state.analysis_result.get("battle_time_text") or "",
                help="예: 06:31 또는 7:15",
                key="battle_time_input",
            )
            back_attack_rate = None
            if selected_class == "블레이드":
                back_attack_rate = st.number_input(
                    "백어택 적중률 (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=st.session_state.analysis_result.get("back_attack_rate") or 0.0,
                    step=0.1,
                    key="back_attack_input",
                )

        with col2:
            st.write("**공격 정보 분석 결과:**")
            extracted_count = st.session_state.analysis_result.get("key_action_count") or 0
            key_action_count = st.number_input(
                action_label_map[selected_class],
                min_value=0,
                value=extracted_count,
                step=1,
                key="key_action_count_input",
            )
            st.write(f"**핵심 행동:** {st.session_state.analysis_result.get('key_action_name')}")

        if not st.session_state.analysis_result.get("summary_ocr_raw") and not st.session_state.analysis_result.get("attack_ocr_raw"):
            st.warning("OCR에서 값을 추출하지 못했습니다. 아래 입력창으로 직접 입력해주세요.")

        with st.expander("📋 OCR 원문 보기"):
            st.write("**종합 정보 OCR:**")
            st.code(st.session_state.analysis_result.get("summary_ocr_raw", ""))
            st.write("**공격 정보 OCR:**")
            st.code(st.session_state.analysis_result.get("attack_ocr_raw", ""))

        battle_time_minutes = parse_battle_time_to_minutes(battle_time_str) if battle_time_str else 0.0
        if battle_time_minutes > 0 and key_action_count > 0:
            key_action_cpm = calculate_cpm(key_action_count, battle_time_minutes)
            st.success(f"✓ 핵심 행동 CPM: {key_action_cpm:.2f} (사용 횟수: {key_action_count}, 전투 시간: {battle_time_minutes:.2f}분)")
        elif battle_time_minutes > 0:
            key_action_cpm = 0.0
            st.info("사용 횟수를 입력하거나 0 이상으로 수정해주세요.")
        else:
            key_action_cpm = 0.0
            st.warning("전투 시간을 정확히 입력해주세요.")

        ocr_raw_text = f"Summary:\n{st.session_state.analysis_result.get('summary_ocr_raw', '')}\n\nAttack:\n{st.session_state.analysis_result.get('attack_ocr_raw', '')}"

        if st.button("✅ 최종 저장"):
            if not selected_class or not selected_boss:
                st.warning("직업과 레이드를 모두 선택해주세요.")
            elif battle_time_minutes <= 0:
                st.warning("전투 시간을 정확히 입력해주세요.")
            else:
                boss_id = next((b["id"] for b in bosses if b["boss_display_name"] == selected_boss), None)
                final_score = 0.0
                warning_shown = False
                if not boss_id:
                    st.warning("선택한 레이드 정보를 찾을 수 없습니다.")
                    warning_shown = True
                try:
                    rules = load_score_rules(selected_class)
                    baselines = load_baselines(selected_class, boss_id)
                    if not rules or not baselines:
                        if not rules:
                            st.warning("선택한 직업의 score_rules 데이터가 없습니다.")
                        if not baselines:
                            st.warning("선택한 직업/레이드에 해당하는 scoring_baselines 데이터가 없습니다.")
                        warning_shown = True
                    else:
                        try:
                            final_score = calculate_final_score(
                                selected_class,
                                rules,
                                baselines,
                                key_action_cpm,
                                back_attack_rate,
                                None,
                            )
                        except Exception as score_error:
                            st.warning(f"점수 계산에 실패했습니다: {score_error}")
                            final_score = 0.0
                            warning_shown = True
                except Exception as e:
                    st.warning(f"점수 계산 중 오류가 발생했습니다: {e}")
                    final_score = 0.0
                    warning_shown = True

                if not warning_shown:
                    st.success("점수 계산이 완료되었습니다.")

                st.session_state["analysis_result"] = {
                    "class_name": selected_class,
                    "boss_id": boss_id,
                    "boss_name_raw": selected_boss,
                    "battle_time_text": battle_time_str,
                    "battle_time_minutes": battle_time_minutes,
                    "key_action_name": key_action_name_map[selected_class],
                    "key_action_count": key_action_count,
                    "key_action_cpm": key_action_cpm,
                    "back_attack_rate": back_attack_rate,
                    "head_attack_rate": None,
                    "final_score": final_score,
                    "score_version": "v1",
                    "video_url": video_url,
                    "screenshot_url": "mock://uploaded_screenshot.png",
                    "ocr_raw_text": ocr_raw_text,
                    "ocr_status": st.session_state.analysis_result.get("ocr_status", "ocr_failed"),
                }
                st.session_state.analysis_step = None
                st.success("분석이 완료되었습니다. 분석 결과 화면으로 이동해주세요.")

else:
    if selected_class:
        mock_metrics = extract_mock_combat_metrics(selected_class)
        key_action_cpm = st.number_input("핵심 행동 CPM", min_value=0.0, value=mock_metrics["key_action_cpm"])
        back_attack_rate = None
        head_attack_rate = None
        if selected_class == "블레이드":
            back_attack_rate = st.number_input(
                "백어택 적중률",
                min_value=0.0,
                max_value=100.0,
                value=mock_metrics["back_attack_rate"] or 0.0,
            )
        if selected_class == "브레이커":
            head_attack_rate = st.number_input(
                "헤드어택 적중률",
                min_value=0.0,
                max_value=100.0,
                value=mock_metrics["head_attack_rate"] or 0.0,
            )
    else:
        key_action_cpm = 0.0
        back_attack_rate = None
        head_attack_rate = None

    if st.button("분석 실행하기"):
        if not uploaded_file:
            st.warning("스크린샷 파일을 업로드해주세요.")
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
                        selected_class,
                        rules,
                        baselines,
                        key_action_cpm,
                        back_attack_rate,
                        head_attack_rate,
                    )
                    # attempt to upload the single uploaded_file to storage
                    screenshot_url = "mock://uploaded_screenshot.png"
                    try:
                        screenshot_url = upload_combat_screenshot(uploaded_file, user["id"], label="summary")
                    except Exception as e:
                        st.error("스크린샷 업로드 중 오류가 발생했습니다.")
                        st.caption(str(e))

                    st.session_state["analysis_result"] = {
                        "class_name": selected_class,
                        "boss_id": boss_id,
                        "video_url": video_url,
                        "key_action_cpm": key_action_cpm,
                        "back_attack_rate": back_attack_rate,
                        "head_attack_rate": head_attack_rate,
                        "final_score": final_score,
                        "ocr_raw_text": ocr_result["ocr_raw_text"],
                        "screenshot_url": screenshot_url,
                    }
                    st.success("분석이 완료되었습니다. 분석 결과 화면으로 이동해주세요.")
            except Exception as e:
                st.error(f"분석 중 오류 발생: {e}")
