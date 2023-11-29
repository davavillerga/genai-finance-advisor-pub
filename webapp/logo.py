import streamlit as st

def add_logo():
    st.markdown(
        """
        <style>
            [data-testid="stSidebarNav"] {
                background-image: url(https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRaa_wP9P2ADvwIzNVL7BBlvc1ZaYsh33HI22Nga4ZHkJe7XgpUNvr_FS-tUPfolA8gg1k&usqp=CAU);
                background-repeat: no-repeat;
                padding-top: 120px;
                background-position: 20px 20px;
            }
            [data-testid="stSidebarNav"]::before {
                content: "Cymbal Investments";
                margin-left: 0px;
                margin-right: 20px;
                margin-top: 0px;
                font-size: 30px;
                position: relative;
                top: 100px;
                width: 120px;
                heigt: 100px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )