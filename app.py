import streamlit as st
from lib.utils import render_sidebar

st.set_page_config(page_title="로스트아크 전투 분석기 플랫폼", layout="wide")

render_sidebar()

st.title("로스트아크 전투 분석기 플랫폼")
st.info(
    "전투 분석기 스크린샷 기반 기록 저장\n"
    "- 행동 기반 점수 계산\n"
    "- 동일 직업/동일 레이드 기준 비교\n"
    "- 영상 링크 기반 랭킹 후보 구조"
)

st.subheader("주요 기능")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("기록 업로드"):
        st.switch_page("pages/2_upload.py")

with col2:
    if st.button("랭킹 보기"):
        st.switch_page("pages/1_ranking.py")

with col3:
    if st.button("내 기록 확인"):
        st.switch_page("pages/4_my_records.py")

st.caption(
    "* 본 프로젝트는 기본틀 시연용입니다. 실제 로그인, OCR, Storage 기능은 mock 처리되어 있습니다."
)