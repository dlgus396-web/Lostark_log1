import streamlit as st
from lib.utils import render_sidebar

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
    st.info("기본틀에서는 실제 DB 저장 없이 mock 저장 흐름만 표시합니다.")
    if st.button("mock 저장 완료 처리"):
        st.success("기본틀에서는 실제 DB 저장 없이 저장 완료 흐름만 표시합니다.")
