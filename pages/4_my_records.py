import streamlit as st
from lib.auth import get_current_user
from lib.db_queries import load_my_records, load_boss_map
from lib.utils import render_sidebar, format_created_date

render_sidebar()

st.title("내 기록")

user = get_current_user()
if not user:
    st.info("로그인이 필요합니다. 로그인 후 내 기록을 확인할 수 있습니다.")
    st.stop()

try:
    records = load_my_records(user["id"])
    boss_map = load_boss_map()
    if not records:
        st.info("아직 저장된 전투 기록이 없습니다.")
    else:
        character_names = [rec.get("character_name") for rec in records if rec.get("character_name")]
        character_options = ["전체"] + sorted(set(character_names), key=lambda x: x.lower())
        selected_character = st.selectbox("캐릭터 선택", character_options)

        # build raid filter options from this user's records
        present_boss_ids = []
        for rec in records:
            bid = rec.get("boss_id")
            if bid is not None and bid not in present_boss_ids:
                present_boss_ids.append(bid)

        boss_filter_options = [{"label": "전체", "id": None}]
        for bid in present_boss_ids:
            boss_filter_options.append({"label": boss_map.get(bid, "-"), "id": bid})

        boss_labels = [opt["label"] for opt in boss_filter_options]
        selected_raid_label = st.selectbox("레이드 선택", boss_labels, index=0)
        selected_raid_id = next((opt["id"] for opt in boss_filter_options if opt["label"] == selected_raid_label), None)

        # apply character filter first
        filtered_records = (
            records
            if selected_character == "전체"
            else [rec for rec in records if rec.get("character_name") == selected_character]
        )

        # then apply raid filter
        if selected_raid_id is not None:
            filtered_records = [rec for rec in filtered_records if rec.get("boss_id") == selected_raid_id]

        if not filtered_records:
            st.info("선택한 캐릭터의 기록이 없습니다.")
        else:
            display_data = []
            for rec in filtered_records:
                display_data.append({
                    "캐릭터명": rec.get("character_name") or "-",
                    "직업": rec.get("class_name"),
                    "레이드": boss_map.get(rec.get("boss_id"), "-"),
                    "최종점수": rec.get("final_score"),
                    "핵심행동CPM": rec.get("key_action_cpm"),
                    "백어택률": rec.get("back_attack_rate") if rec.get("class_name") == "블레이드" and rec.get("back_attack_rate") is not None else "-",
                    "생성일": format_created_date(rec.get("created_at")),
                })
            st.dataframe(display_data, use_container_width=True)

            st.divider()
            for i, rec in enumerate(filtered_records):
                title_name = rec.get("character_name") or "-"
                raid_display = boss_map.get(rec.get('boss_id'), '-')
                with st.expander(f"상세 보기 - {title_name} / {rec.get('class_name', 'N/A')} / {raid_display} / 점수 {rec.get('final_score', 'N/A')}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**캐릭터명:** {rec.get('character_name') or '-'}")
                        st.write(f"**직업:** {rec.get('class_name')}")
                        st.write(f"**레이드:** {raid_display}")
                        st.write(f"**최종 점수:** {rec.get('final_score')}")
                    with col2:
                        st.write(f"**핵심 행동 CPM:** {rec.get('key_action_cpm')}")
                        st.write(f"**백어택률:** {rec.get('back_attack_rate') if rec.get('class_name') == '블레이드' and rec.get('back_attack_rate') is not None else '-'}")
                        st.write(f"**생성일:** {format_created_date(rec.get('created_at'))}")
                    if rec.get('video_url'):
                        st.write(f"**영상 링크:** [링크]({rec.get('video_url')})")
except Exception as e:
    st.error("내 기록 데이터를 불러오지 못했습니다.")
    st.caption(str(e))
