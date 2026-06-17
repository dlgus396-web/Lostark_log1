import streamlit as st
from lib.supabase_client import get_supabase_client


def _extract_user(auth_response):
    if not auth_response:
        return None

    user_obj = getattr(auth_response, "user", None)
    if user_obj is None and isinstance(auth_response, dict):
        user_obj = auth_response.get("user")
    if not user_obj:
        return None

    user_id = getattr(user_obj, "id", None)
    if user_id is None and isinstance(user_obj, dict):
        user_id = user_obj.get("id")

    email = getattr(user_obj, "email", None)
    if email is None and isinstance(user_obj, dict):
        email = user_obj.get("email")

    if not user_id:
        return None

    return {"id": user_id, "email": email}


def sign_up_with_email(email: str, password: str):
    if not email or not password:
        raise ValueError("이메일과 비밀번호를 모두 입력해주세요.")

    supabase = get_supabase_client()
    auth_response = supabase.auth.sign_up({"email": email, "password": password})
    user = _extract_user(auth_response)
    if not user:
        raise RuntimeError("회원가입에 실패했습니다.")

    ensure_profile(user)
    st.session_state["user"] = user
    return user


def sign_in_with_email(email: str, password: str):
    if not email or not password:
        raise ValueError("이메일과 비밀번호를 모두 입력해주세요.")

    supabase = get_supabase_client()
    auth_response = supabase.auth.sign_in_with_password({"email": email, "password": password})
    user = _extract_user(auth_response)
    if not user:
        raise RuntimeError("로그인에 실패했습니다.")

    ensure_profile(user)
    st.session_state["user"] = user
    return user


def sign_out():
    supabase = get_supabase_client()
    try:
        supabase.auth.sign_out()
    except Exception:
        pass

    st.session_state.pop("user", None)


def get_current_user():
    current_user = st.session_state.get("user")
    if current_user:
        return current_user

    try:
        supabase = get_supabase_client()
        user = supabase.auth.get_user()
    except Exception:
        return None

    if not user:
        return None

    user_id = getattr(user, "id", None)
    if user_id is None and isinstance(user, dict):
        user_id = user.get("id")

    email = getattr(user, "email", None)
    if email is None and isinstance(user, dict):
        email = user.get("email")

    if not user_id:
        return None

    current_user = {"id": user_id, "email": email}
    st.session_state["user"] = current_user
    return current_user


def ensure_profile(user):
    if not user or not user.get("id"):
        raise ValueError("유효한 사용자가 필요합니다.")

    supabase = get_supabase_client()
    user_id = user["id"]

    try:
        profile_result = (
            supabase.table("profiles")
            .select("id")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        existing_profiles = getattr(profile_result, "data", None)
        if existing_profiles is None and isinstance(profile_result, dict):
            existing_profiles = profile_result.get("data")

        if existing_profiles:
            return existing_profiles[0]

        display_name = user.get("email", "")
        if display_name and "@" in display_name:
            display_name = display_name.split("@", 1)[0]
        if not display_name:
            display_name = user_id[:8]

        profile_data = {
            "id": user_id,
            "discord_user_id": None,
            "display_name": display_name,
            "avatar_url": None,
        }
        supabase.table("profiles").insert(profile_data).execute()
        return profile_data
    except Exception:
        return None
