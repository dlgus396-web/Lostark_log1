import streamlit as st
from lib.utils import render_sidebar
from lib.db_queries import insert_combat_record
from lib.auth import get_current_user

render_sidebar()

st.title("분석 결과")

result = st.session_state.get("analysis_result")
user = get_current_user()
if not result:
    st.warning("아직 분석 결과가 없습니다. 먼저 기록 업로드 화면에서 분석을 실행해주세요.")
    if not user:
        st.info("로그인이 필요한 경우 로그인 페이지로 이동해주세요.")
else:
    if not user:
        st.info("로그인하면 분석 결과를 DB에 저장할 수 있습니다. 로그인 페이지로 이동해주세요.")

    st.metric("최종 점수", f"{result['final_score']:.2f}")

    # 깔끔한 레이아웃: 주요 정보들을 두 칼럼으로 배치
    left, right = st.columns([2, 1])

    with left:
        st.write(f"**캐릭터명:** {result.get('character_name', '-')} ")
        st.write(f"**직업:** {result.get('class_name', '-')} ")
        st.write(f"**레이드:** {result.get('boss_name_raw') or result.get('boss_id')}")
        st.write(f"**전투 시간:** {result.get('battle_time_text') or 'N/A'}")

    with right:
        st.write(f"**핵심 행동:** {result.get('key_action_name', '-')}")
        st.write(f"**핵심 행동 사용 횟수:** {result.get('key_action_count', 0)}")
        st.write(f"**핵심 행동 CPM:** {result.get('key_action_cpm', 0)}")
        # 백어택률은 블레이드일 때만 표시
        if result.get('class_name') == '블레이드' and result.get('back_attack_rate') is not None:
            st.write(f"**백어택 적중률:** {result['back_attack_rate']}")

    # 영상 링크는 입력된 경우에만 표시
    if result.get('video_url'):
        st.write(f"**영상 링크:** {result['video_url']}")
    st.info("OCR 결과는 사용자가 확인 및 수정할 수 있으며, 최종 분석 기록은 DB에 저장됩니다.")
    def normalize_ocr_status_for_db(status: str | None) -> str:
        """Normalize various ocr_status inputs to either 'success' or 'fallback_used'.

        Rules:
        - if status == 'success' -> 'success'
        - if status == 'fallback_used' -> 'fallback_used'
        - if 'success' in status -> 'success'
        - otherwise -> 'fallback_used'
        """
        if not status:
            return "fallback_used"
        s = str(status).lower()
        if s == "success":
            return "success"
        if s == "fallback_used":
            return "fallback_used"
        if "success" in s:
            return "success"
        return "fallback_used"

    # build record only with allowed columns for combat_records
    # Hide mock screenshot URL from display; normalize mock to None for DB
    screenshot_url = result.get("screenshot_url")
    if screenshot_url == "mock://uploaded_screenshot.png":
        screenshot_url = None

    record = {
        "user_id": user["id"] if user else None,
        "class_name": result.get("class_name"),
        "boss_id": result.get("boss_id"),
        "boss_name_raw": result.get("boss_name_raw") or str(result.get("boss_id")),
        "character_name": result.get("character_name"),
        "screenshot_url": screenshot_url,
        "ocr_raw_text": result.get("ocr_raw_text"),
        # normalize to DB-allowed values
        "ocr_status": normalize_ocr_status_for_db(result.get("ocr_status")),
        "final_score": result.get("final_score"),
        "key_action_cpm": result.get("key_action_cpm"),
        "back_attack_rate": result.get("back_attack_rate"),
        "score_version": result.get("score_version") or "v1",
        "video_url": result.get("video_url"),
    }

    # Ensure only allowed DB columns are present (attack_screenshot_url excluded)

    with st.expander("DB 저장 데이터 확인"):
        st.json(record)

    if user and st.button("DB에 기록 저장"):
        try:
            insert_combat_record(record)
            st.success("전투 기록이 DB에 저장되었습니다.")
        except Exception as e:
            st.error("전투 기록 저장 중 오류가 발생했습니다.")
            st.caption(str(e))
    elif not user:
        st.info("로그인한 사용자만 분석 결과를 DB에 저장할 수 있습니다.")
