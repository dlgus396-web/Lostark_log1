import streamlit as st
from lib.utils import render_sidebar
from lib.auth import sign_up_with_email, sign_in_with_email, sign_out, get_current_user

render_sidebar()

st.title("로그인")

user = get_current_user()

if user:
    st.success(f"로그인됨: {user.get('email')}")
    st.write("로그아웃하면 다른 계정으로 다시 로그인할 수 있습니다.")
    if st.button("로그아웃"):
        sign_out()
        st.success("로그아웃되었습니다.")
        st.experimental_rerun()
    st.info("기록 업로드와 내 기록 조회는 로그인 후에 이용할 수 있습니다.")
else:
    email = st.text_input("이메일", key="login_email")
    password = st.text_input("비밀번호", type="password", key="login_password")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("회원가입"):
            if not email or not password:
                st.warning("이메일과 비밀번호를 모두 입력해주세요.")
            else:
                try:
                    sign_up_with_email(email, password)
                    st.success("회원가입 및 로그인에 성공했습니다.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"회원가입 중 오류가 발생했습니다: {e}")
    with col2:
        if st.button("로그인"):
            if not email or not password:
                st.warning("이메일과 비밀번호를 모두 입력해주세요.")
            else:
                try:
                    sign_in_with_email(email, password)
                    st.success("로그인에 성공했습니다.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"로그인 중 오류가 발생했습니다: {e}")

    st.markdown(
        "로그인 후 기록 업로드, 분석 결과 저장, 내 기록 조회 기능을 이용할 수 있습니다."
    )
