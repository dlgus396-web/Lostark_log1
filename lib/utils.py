import streamlit as st

def render_sidebar():
    st.sidebar.title("로스트아크 전투 분석기 플랫폼")
    user = st.session_state.get("user")
    if user:
        st.sidebar.caption(f"로그인됨: {user.get('email')}")
    else:
        st.sidebar.caption("로그인되지 않음")

    st.sidebar.page_link("app.py", label="홈", icon="🏠")
    st.sidebar.page_link("pages/0_login.py", label="로그인", icon="🔐")
    st.sidebar.page_link("pages/1_ranking.py", label="랭킹", icon="🏆")
    st.sidebar.page_link("pages/2_upload.py", label="기록 업로드", icon="📤")
    st.sidebar.page_link("pages/3_analysis_result.py", label="분석 결과", icon="🔎")
    st.sidebar.page_link("pages/4_my_records.py", label="내 기록", icon="📒")


def format_score(score: float) -> str:
    return f"{score:.2f}"


def render_score_card(title: str, value: str, description: str = ""):
    st.metric(label=title, value=value, help=description)


def render_empty_state(message: str):
    st.info(message)


def format_created_date(created_at: str | None) -> str:
    """Format ISO datetime string to YYYY/MM/DD or return '-' on failure.

    Examples:
      2026-06-19T04:15:24.126204+00:00 -> 2026/06/19
    """
    if not created_at:
        return "-"
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(created_at)
        return dt.strftime("%Y/%m/%d")
    except Exception:
        # fallback: try first 10 chars YYYY-MM-DD
        try:
            if isinstance(created_at, str) and len(created_at) >= 10:
                date_str = created_at[:10]
                from datetime import datetime
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                return dt.strftime("%Y/%m/%d")
        except Exception:
            pass
    return "-"