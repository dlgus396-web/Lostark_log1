import streamlit as st
from lib.db_queries import load_my_records
from lib.utils import render_sidebar
from lib.auth import get_current_user

render_sidebar()

st.title("내 기록")

user = get_current_user()
if not user:
    st.warning("내 기록 조회를 위해 로그인해주세요.")
    st.stop()

st.caption(f"현재 사용자: {user.get('email')}")

try:
    records = load_my_records(user["id"])
    if not records:
        st.info("아직 저장된 전투 기록이 없습니다.")
    else:
        # Display dataframe with key columns
        display_data = []
        for rec in records:
            display_data.append({
                "직업": rec.get("class_name"),
                "레이드": rec.get("boss_id"),
                "최종점수": rec.get("final_score"),
                "핵심행동CPM": rec.get("key_action_cpm"),
                "백어택률": rec.get("back_attack_rate"),
                "헤드어택률": rec.get("head_attack_rate"),
                "생성일": rec.get("created_at"),
            })
        st.dataframe(display_data, use_container_width=True)
        
        # Display expandable details for each record
        st.divider()
        for i, rec in enumerate(records):
            with st.expander(f"상세 보기 - {rec.get('class_name', 'N/A')} (점수: {rec.get('final_score', 'N/A')}) - {rec.get('created_at', 'N/A')}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**직업:** {rec.get('class_name')}")
                    st.write(f"**레이드 ID:** {rec.get('boss_id')}")
                    st.write(f"**최종 점수:** {rec.get('final_score')}")
                    st.write(f"**핵심 행동 CPM:** {rec.get('key_action_cpm')}")
                with col2:
                    st.write(f"**백어택률:** {rec.get('back_attack_rate')}")
                    st.write(f"**헤드어택률:** {rec.get('head_attack_rate')}")
                    st.write(f"**생성일:** {rec.get('created_at')}")
                if rec.get('video_url'):
                    st.write(f"**영상 링크:** [링크]({rec.get('video_url')})")
except Exception as e:
    st.error("내 기록 데이터를 불러오지 못했습니다.")
    st.caption(str(e))
