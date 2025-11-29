# import streamlit as st
# from userInterface.login_pg import login_page
# from userInterface.filter_ui import asteroid_app_page


# def main():
#     st.set_page_config(
#         page_title="NASA Asteroid Tracker",
#         page_icon="🪐",
#         layout="wide",
#     )

#     if "logged_in" not in st.session_state:
#         st.session_state.logged_in = False
#         st.session_state.username = ""

#     if not st.session_state.logged_in:
#         login_page()
#     else:
#         asteroid_app_page()


# if __name__ == "__main__":
#     main()

import streamlit as st
from userInterface.login_pg import login_page
from userInterface.filter_ui import asteroid_app_page


def main():
    st.set_page_config(
        page_title="NASA Asteroid Tracker",
        page_icon="🪐",
        layout="wide",
    )

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ""

    if not st.session_state.logged_in:
        login_page()
    else:
        asteroid_app_page()


if __name__ == "__main__":
    main()
