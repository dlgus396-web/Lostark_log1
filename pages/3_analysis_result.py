import streamlit as st
from lib.utils import render_sidebar
from lib.db_queries import insert_combat_record

# 임시 로그인 미구현 상태를 위한 테스트 유저 ID (나중에 실제 profiles.id로 교체)
MOCK_USER_ID = "여기에_profiles_id_입력"

render_sidebar()

st.title("분석 결과")

result = st.session_state.get("analysis_result")
if not result:
    st.warning("아직 분석 결과가 없습니다. 먼저 기록 업로드 화면에서 분석을 실행해주세요.")
else:
    st.metric("최종 점수", f"{result['final_score']:.2f}")
    st.write(f"**직업:** {result['class_name']}")
    st.write(f"**레이드:** {result['boss_id']}")
    st.write(f"**핵심 행동 CPM:** {result['key_action_cpm']}")
    if result.get("back_attack_rate") is not None:
        st.write(f"**백어택률:** {result['back_attack_rate']}")
    if result.get("head_attack_rate") is not None:
        st.write(f"**헤드어택률:** {result['head_attack_rate']}")
    if result.get("video_url"):
        st.write(f"**영상 링크:** {result['video_url']}")
    st.write(f"**OCR 원문:** {result['ocr_raw_text']}")
    st.info("로그인/ OCR/ Storage 업로드는 mock 상태입니다. DB 저장만 실제로 시도합니다.")
    if st.button("DB에 기록 저장"):
        try:
            record = {
                "user_id": MOCK_USER_ID,
                "class_name": result.get("class_name"),
                "boss_id": result.get("boss_id"),
                "boss_name_raw": str(result.get("boss_id")) if result.get("boss_id") is not None else "mock boss",
                "screenshot_url": result.get("screenshot_url"),
                "ocr_raw_text": result.get("ocr_raw_text"),
                "ocr_status": "mock_success",
                "final_score": result.get("final_score"),
                "key_action_cpm": result.get("key_action_cpm"),
                "back_attack_rate": result.get("back_attack_rate"),
                "head_attack_rate": result.get("head_attack_rate"),
                "score_version": "v1",
                "video_url": result.get("video_url"),
            }
            insert_combat_record(record)
            st.success("전투 기록이 DB에 저장되었습니다.")
        except Exception as e:
            st.error("전투 기록 저장 중 오류가 발생했습니다.")
            st.caption(str(e))
