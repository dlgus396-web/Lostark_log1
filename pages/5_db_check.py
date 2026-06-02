import streamlit as st
from lib.utils import render_sidebar
from lib.db_queries import load_supported_classes, load_bosses, load_score_rules, load_baselines
from lib.scoring import calculate_final_score

render_sidebar()

st.title("DB 상태 확인")

classes = []
bosses = []
try:
    classes = load_supported_classes()
    st.subheader("지원 직업 조회 결과")
    st.write(classes)
except Exception as e:
    st.error("지원 직업 데이터를 불러오지 못했습니다.")
    st.caption(str(e))

try:
    bosses = load_bosses()
    st.subheader("지원 레이드 조회 결과")
    st.write(bosses)
except Exception as e:
    st.error("레이드 데이터를 불러오지 못했습니다.")
    st.caption(str(e))

selected_class = st.selectbox("직업 선택(테스트)", [c["class_name"] for c in classes] if classes else [])
selected_boss_id = st.selectbox("레이드 선택(테스트)", [b["id"] for b in bosses] if bosses else [])

if selected_class and selected_boss_id:
    try:
        rules = load_score_rules(selected_class)
        baselines = load_baselines(selected_class, selected_boss_id)
        st.subheader("점수 규칙 조회 결과")
        st.write(rules)
        st.subheader("기준 데이터 조회 결과")
        st.write(baselines)
        if rules and baselines:
            score = calculate_final_score(selected_class, rules, baselines, 5.0, 80.0, 80.0)
            st.metric("테스트 점수", f"{score:.2f}")
    except Exception as e:
        st.error(f"점수 계산 테스트 중 오류: {e}")
