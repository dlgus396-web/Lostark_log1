def render_sidebar():
    import streamlit as st

    st.sidebar.title("로스트아크 전투 분석기 플랫폼")
    st.sidebar.caption("현재 상태: Mock Login")

    st.sidebar.page_link("app.py", label="홈", icon="🏠")
    st.sidebar.page_link("pages/1_ranking.py", label="랭킹", icon="🏆")
    st.sidebar.page_link("pages/2_upload.py", label="기록 업로드", icon="📤")
    st.sidebar.page_link("pages/3_analysis_result.py", label="분석 결과", icon="🔎")
    st.sidebar.page_link("pages/4_my_records.py", label="내 기록", icon="📒")
    st.sidebar.page_link("pages/5_db_check.py", label="DB 상태 확인", icon="🗄️")


def format_score(score: float) -> str:
    return f"{score:.2f}"


def render_score_card(title: str, value: str, description: str = ""):
    st.metric(label=title, value=value, help=description)


def render_empty_state(message: str):
    st.info(message)