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
    st.write(f"**직업:** {result['class_name']}")
    st.write(f"**레이드:** {result.get('boss_name_raw') or result.get('boss_id')}")
    st.write(f"**전투 시간:** {result.get('battle_time_text') or 'N/A'}")
    st.write(f"**핵심 행동:** {result.get('key_action_name')}")
    st.write(f"**핵심 행동 사용 횟수:** {result.get('key_action_count')}")
    st.write(f"**핵심 행동 CPM:** {result.get('key_action_cpm')}")
    if result.get("back_attack_rate") is not None:
        st.write(f"**백어택 적중률:** {result['back_attack_rate']}")
    if result.get("head_attack_rate") is not None:
        st.write(f"**헤드어택 적중률:** {result['head_attack_rate']}")
    if result.get("video_url"):
        st.write(f"**영상 링크:** {result['video_url']}")
    st.write(f"**OCR 원문:** {result['ocr_raw_text']}")
    st.info("로그인/ OCR/ Storage 업로드는 mock 상태입니다. DB 저장만 실제로 시도합니다.")
    if user and st.button("DB에 기록 저장"):
        try:
            record = {
                "user_id": user["id"],
                "class_name": result.get("class_name"),
                "boss_id": result.get("boss_id"),
                "boss_name_raw": result.get("boss_name_raw") or str(result.get("boss_id")),
                "screenshot_url": result.get("screenshot_url"),
                "ocr_raw_text": result.get("ocr_raw_text"),
                "ocr_status": result.get("ocr_status") or "ocr_failed",
                "final_score": result.get("final_score"),
                "key_action_cpm": result.get("key_action_cpm"),
                "back_attack_rate": result.get("back_attack_rate"),
                "head_attack_rate": result.get("head_attack_rate"),
                "score_version": result.get("score_version") or "v1",
                "video_url": result.get("video_url"),
            }
            insert_combat_record(record)
            st.success("전투 기록이 DB에 저장되었습니다.")
        except Exception as e:
            st.error("전투 기록 저장 중 오류가 발생했습니다.")
            st.caption(str(e))
    elif not user:
        st.info("로그인한 사용자만 분석 결과를 DB에 저장할 수 있습니다.")
