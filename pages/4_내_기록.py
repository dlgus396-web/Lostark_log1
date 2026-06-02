import streamlit as st
from lib.db_queries import load_mock_my_records
from lib.utils import render_empty_state

st.title("내 기록")
st.caption("현재 사용자: Mock User")

records = load_mock_my_records()
if not records:
    render_empty_state("mock 내 기록 데이터가 없습니다.")
else:
    st.dataframe(records)
    st.caption("* 본 화면은 mock 데이터 기반입니다.")
    for rec in records:
        with st.expander(f"상세 보기 - {rec['class_name']} / {rec['raid_name']}"):
            st.write(rec)
st.title("내 기록")
st.caption("현재 사용자: Mock User")

records = load_mock_my_records()
if not records:
    render_empty_state("mock 내 기록 데이터가 없습니다.")
else:
    st.dataframe(records)
    st.caption("* 본 화면은 mock 데이터 기반입니다.")
    for rec in records:
        with st.expander(f"상세 보기 - {rec['class_name']} / {rec['raid_name']}"):
            st.write(rec)
