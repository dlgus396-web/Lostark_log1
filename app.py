import streamlit as st
import random
from lib.utils import render_sidebar
from lib.db_queries import load_ranking_records, load_my_records, load_bosses

st.set_page_config(page_title="로스트아크 전투 분석기 플랫폼", layout="wide")

render_sidebar()

st.title("로스트아크 전투 분석기 플랫폼")
st.info(
    "전투 분석기 스크린샷 기반 기록 저장\n"
    "- OCR 기반 핵심 지표 추출\n"
    "- 행동 기반 점수 계산\n"
    "- 영상 링크 기반 랭킹 후보 제공"
)

# 상위 랭킹 미리보기 (전체폭)
st.subheader("상위 랭킹 미리보기")
try:
    records = load_ranking_records()
except Exception as e:
    st.warning("랭킹 미리보기를 불러오지 못했습니다.")
    st.caption(str(e))
    records = None

if not records:
    st.info("아직 랭킹에 표시할 기록이 없습니다.")
else:
    # 가능한 (레이드, 직업) 조합만 수집하고 그 중 하나를 선택
    try:
        bosses = load_bosses()
        boss_map = {b.get("id"): b for b in bosses}
    except Exception:
        bosses = []
        boss_map = {}

    pairs = []
    for r in records:
        raid_label = r.get("raid_name") or r.get("boss_display_name")
        cls = r.get("class_name")
        boss_id = r.get("boss_id") or r.get("boss") or r.get("boss_id")
        boss_entry = boss_map.get(boss_id)
        gate_label = None
        if boss_entry:
            raid_label = boss_entry.get("raid_name") or raid_label
            gate_label = boss_entry.get("boss_display_name")

        if raid_label and cls:
            pairs.append((raid_label, gate_label or raid_label, cls))

    pairs = list(dict.fromkeys(pairs))  # 중복 제거

    if not pairs:
        st.info("표시할 랭킹 데이터가 없습니다.")
    else:
        chosen = random.choice(pairs)
        chosen_raid, chosen_gate, chosen_class = chosen
        label = chosen_gate or chosen_raid
        st.info(f"{label} / {chosen_class}")

        filtered = [r for r in records if (r.get("raid_name") == chosen_raid or (boss_map.get(r.get("boss_id")) and boss_map.get(r.get("boss_id")).get("raid_name") == chosen_raid)) and r.get("class_name") == chosen_class]

        if not filtered:
            st.info("선택된 관문/직업의 랭킹이 없습니다.")
        else:
            try:
                if all("rank" in r for r in filtered):
                    filtered = sorted(filtered, key=lambda x: x.get("rank"))
                else:
                    filtered = sorted(filtered, key=lambda x: x.get("final_score") or 0, reverse=True)
            except Exception:
                pass

            display = []
            for idx, rec in enumerate(filtered[:5], start=1):
                boss_id = rec.get("boss_id")
                boss_entry = boss_map.get(boss_id)
                raid_name = boss_entry.get("raid_name") if boss_entry else (rec.get("raid_name") or rec.get("boss_display_name"))
                gate_name = boss_entry.get("boss_display_name") if boss_entry else None
                display.append(
                    {
                        "순위": idx,
                        "캐릭터명": rec.get("character_name") or "-",
                        "직업": rec.get("class_name"),
                        "레이드": raid_name,
                        "관문": gate_name or raid_name,
                        "최종 점수": rec.get("final_score"),
                        "핵심 행동 CPM": rec.get("key_action_cpm"),
                    }
                )
            st.table(display)

if st.button("전체 랭킹 보기"):
    st.switch_page("pages/1_ranking.py")

# 구분선
st.markdown("---")

# 로그인 / 내 기록 섹션 (하단)
st.subheader("로그인 / 내 최근 기록")
user = st.session_state.get("user")
if not user:
    st.info("로그인이 필요합니다.")
    st.write("로그인하면 기록 업로드, 분석 결과 저장, 내 기록 조회를 사용할 수 있습니다.")
    if st.button("로그인하러 가기"):
        st.switch_page("pages/0_login.py")
else:
    st.write(f"현재 로그인: {user.get('email', '알 수 없음')}")
    try:
        my_records = load_my_records(user.get("id"))
    except Exception as e:
        st.warning("내 기록 미리보기를 불러오지 못했습니다.")
        st.caption(str(e))
        my_records = None

    if not my_records:
        st.info("아직 저장된 내 기록이 없습니다.")
    else:
        # 최근 3개를 expander로 정리해 가독성 개선
        for rec in my_records[:3]:
            title = f"{rec.get('character_name', '-') or '-'} / {rec.get('class_name', '직업 없음')} — {rec.get('created_at', '')}"
            with st.expander(title):
                st.write(f"**캐릭터명:** {rec.get('character_name') or '-'}")
                st.write(f"**직업:** {rec.get('class_name')}")
                st.write(f"**최종 점수:** {rec.get('final_score')}")
                st.write(f"**핵심 행동 CPM:** {rec.get('key_action_cpm')}")
                st.write(f"**레이드:** {rec.get('raid_name')}")

    if st.button("내 기록 전체 보기"):
        st.switch_page("pages/4_my_records.py")

# 하단의 작게 남기는 기존 네비게이션(선택적)
# 하단 간단 설명만 유지

st.caption(
    "* 본 프로젝트는 기본틀 시연용입니다. 이메일/비밀번호 기반 Supabase 로그인 기능이 구현되어 있으며, OCR 및 Storage는 mock 처리되어 있습니다."
)