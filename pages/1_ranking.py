import streamlit as st
from datetime import datetime
from lib.auth import get_current_user
from lib.db_queries import load_ranking_records, load_supported_classes, load_bosses, insert_report
from lib.utils import render_empty_state, render_sidebar

def format_created_date(created_at: str | None) -> str:
    """Format ISO datetime string to YYYY/MM/DD format.
    
    Args:
        created_at: ISO format datetime string (e.g., 2026-06-17T14:28:37.879381+00:00)
    
    Returns:
        Formatted date string in YYYY/MM/DD format, or "-" if None.
    """
    if created_at is None:
        return "-"
    
    try:
        # Parse ISO format datetime
        dt = datetime.fromisoformat(created_at)
        return dt.strftime("%Y/%m/%d")
    except (ValueError, TypeError):
        # Fallback: use first 10 characters (YYYY-MM-DD) and convert to YYYY/MM/DD
        if isinstance(created_at, str) and len(created_at) >= 10:
            date_str = created_at[:10]  # YYYY-MM-DD
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                return dt.strftime("%Y/%m/%d")
            except ValueError:
                return "-"
        return "-"

render_sidebar()

st.title("상위 랭킹")

try:
    supported_classes = load_supported_classes()
    bosses = load_bosses()
except Exception as e:
    st.error("랭킹 데이터를 불러오지 못했습니다.")
    st.caption(str(e))
    st.stop()

class_options = ["전체"] + [c["class_name"] for c in supported_classes]
boss_options = ["전체"] + [b["boss_display_name"] for b in bosses]

selected_class = st.selectbox("직업 필터", class_options, index=0)
selected_boss = st.selectbox("레이드 필터", boss_options, index=0)

class_filter = None if selected_class == "전체" else selected_class
boss_id = None
if selected_boss != "전체":
    boss_candidate = next((b for b in bosses if b["boss_display_name"] == selected_boss), None)
    boss_id = boss_candidate["id"] if boss_candidate else None

try:
    records = load_ranking_records(class_filter, boss_id)
except Exception as e:
    st.error("랭킹 데이터를 불러오지 못했습니다.")
    st.caption(str(e))
    st.stop()

if not records:
    render_empty_state("랭킹에 표시할 기록이 없습니다. 영상 링크가 포함된 기록을 저장해주세요.")
else:
    display_data = []
    for idx, rec in enumerate(records, start=1):
        display_data.append({
            "순위": idx,
            "캐릭터명": rec.get("character_name") or "-",
            "직업": rec.get("class_name"),
            "레이드 ID": rec.get("boss_id"),
            "최종 점수": rec.get("final_score"),
            "핵심 행동 CPM": rec.get("key_action_cpm"),
            "백어택률": rec.get("back_attack_rate"),
            "영상 링크": rec.get("video_url"),
            "생성일": format_created_date(rec.get("created_at")),
        })

    st.dataframe(display_data, use_container_width=True)
    st.caption("* 영상 링크가 있는 기록만 랭킹에 표시됩니다.")

    user = get_current_user()
    for idx, rec in enumerate(records, start=1):
        record_id = rec.get("id")
        expander_title = f"순위 {idx} - {rec.get('character_name', '-') or '-'} / {rec.get('class_name', 'N/A')} / 점수 {rec.get('final_score', 'N/A')}"
        with st.expander(expander_title):
            st.write(f"**캐릭터명:** {rec.get('character_name') or '-'}")
            st.write(f"**직업:** {rec.get('class_name')}")
            st.write(f"**레이드 ID:** {rec.get('boss_id')}")
            st.write(f"**최종 점수:** {rec.get('final_score')}")
            st.write(f"**핵심 행동 CPM:** {rec.get('key_action_cpm')}")
            st.write(f"**백어택률:** {rec.get('back_attack_rate')}")
            st.write(f"**영상 링크:** {rec.get('video_url')}")
            st.write(f"**생성일:** {format_created_date(rec.get('created_at'))}")
            report_reason_key = f"report_reason_{record_id or idx}"
            report_button_key = f"report_submit_{record_id or idx}"
            report_reason = st.text_area(
                "신고 사유",
                value=st.session_state.get(report_reason_key, ""),
                key=report_reason_key,
                height=120,
            )
            if st.button("신고 제출", key=report_button_key):
                if not user:
                    st.warning("신고하려면 먼저 로그인해주세요.")
                elif not report_reason or not report_reason.strip():
                    st.warning("신고 사유를 입력해주세요.")
                elif not record_id:
                    st.error("신고할 기록 ID를 찾을 수 없습니다.")
                else:
                    try:
                        insert_report(record_id, user["id"], report_reason.strip())
                        st.success("신고가 접수되었습니다.")
                    except Exception as e:
                        error_msg = str(e).lower()
                        if "duplicate" in error_msg or "unique" in error_msg:
                            st.warning("이미 신고한 기록입니다.")
                        else:
                            st.error("신고 저장 중 오류가 발생했습니다.")
                            st.caption(str(e))
