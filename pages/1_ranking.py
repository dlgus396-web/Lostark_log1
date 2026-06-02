import streamlit as st
from lib.db_queries import load_mock_ranking_records
from lib.utils import render_empty_state, render_sidebar

render_sidebar()

st.title("상위 랭킹")

records = load_mock_ranking_records()
if not records:
    render_empty_state("mock 랭킹 데이터가 없습니다.")
else:
    st.dataframe(records)
    st.caption("* 영상 링크가 있는 기록만 랭킹에 표시됩니다.\n* 본 화면은 mock 데이터 기반입니다.")
    for rec in records:
        with st.expander(f"상세 보기 - {rec['class_name']} / {rec['raid_name']}"):
            st.write(rec)
            if st.button("신고", key=f"report_button_{rec['class_name']}"):
                st.info("기본틀에서는 신고 기능이 mock 처리됩니다. 실제 구현 단계에서 reports 테이블에 저장합니다.")
