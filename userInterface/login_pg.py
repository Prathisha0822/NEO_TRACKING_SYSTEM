import streamlit as st

# 🔐 Hard-coded login users
USERS = {
    "admin": "password",
    "kalki": "kalki",
}


def authenticate_user(username: str, password: str) -> bool:
    """Validate user using the USERS dictionary."""
    return username in USERS and USERS[username] == password


def init_session():
    """Initialize session state variables for login."""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ""
    if "remember" not in st.session_state:
        st.session_state.remember = False


def login_page():
    """Render the login UI."""
    init_session()

    st.markdown(
        """
        <style>
        .login-title {
            text-align: center;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
        }
        .login-subtitle {
            text-align: center;
            color: #666;
            font-size: 0.9rem;
            margin-bottom: 1.3rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="login-box">', unsafe_allow_html=True)

    st.markdown(
        '<div class="login-title">☄️ NASA Asteroid Tracker</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="login-subtitle">Sign in ➜</div>',
        unsafe_allow_html=True,
    )

    # ----------- Login Form -----------
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        remember = st.checkbox("Remember me", value=False)
        submitted = st.form_submit_button("Sign In")

    if submitted:
        if authenticate_user(username.strip(), password):
            st.session_state.logged_in = True
            st.session_state.username = username.strip()
            st.session_state.remember = remember
            st.success("Login successful")
            st.rerun()  # correct replacement for experimental_rerun
        else:
            st.error("Invalid username or password")

    st.markdown("</div>", unsafe_allow_html=True)
