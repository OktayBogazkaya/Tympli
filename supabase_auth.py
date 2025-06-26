import streamlit as st
from supabase import create_client, Client

# Supabase setup
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Authentication functions
def sign_up(email: str, password: str):
    try:
        user = supabase.auth.sign_up({"email": email, "password": password})
        if user.user:
            if user.session:  # Session exists if email confirmation is disabled
                st.session_state["user"] = user.user
            else:  # Email confirmation required
                st.session_state["user"] = None
            return user
        else:
            st.error("Signup failed: No user returned.")
            return None
    except Exception as e:
        st.error(f"Registration failed: {str(e)}")
        return None

def sign_in(email: str, password: str):
    try:
        user = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if user.user:
            st.session_state["user"] = user.user
            return user
        else:
            st.error("Login failed: No user returned.")
            return None
    except Exception as e:
        st.error(f"Login failed: {str(e)}")
        return None

def sign_out():
    try:
        supabase.auth.sign_out()
        st.session_state["user"] = None
        st.session_state["user_email"] = None
        #st.success("Logged out successfully!")
        st.rerun()
    except Exception as e:
        st.error(f"Logout failed: {str(e)}")

def auth_screen():
    st.info("""
    ### Welcome to the Beta version!  
    For now, please use a temporary email to sign up. You can get one quickly from [temp-mail.org](https://temp-mail.org/).
    """)
    st.title("Login or Sign Up")
    option = st.selectbox("Choose an option:", ["Login", "Sign Up"])
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    
    if option == "Sign Up" and st.button("Register"):
        user = sign_up(email, password)
        if user and user.user:
            if not user.session:  # Email confirmation required
                st.success("Registration successful! Please verify your email and log in.")
            else:  # Immediate login (no email confirmation)
                st.session_state["user_email"] = user.user.email
                st.success(f"Welcome, {email}!")
                st.rerun()

    if option == "Login" and st.button("Login"):
        user = sign_in(email, password)
        if user and user.user:
            st.session_state["user_email"] = user.user.email
            #st.success(f"Welcome back, {email}!")
            st.rerun()
