# Copyright 2023 Google LLC

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Author: Daniel Villegas, Google 2023

import streamlit as st
from streamlit.components.v1 import html

import config
import matplotlib.pyplot as plt
from langchain.document_loaders import PyPDFLoader

#from io import BytesIO


st.set_page_config(
    page_title="Asesor Financiero",
    page_icon="hello",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
    <style>
        .reportview-container {
            margin-top: -2em;
        }
        #MainMenu {visibility: hidden;}
        .stDeployButton {display:none;}
        footer {visibility: hidden;}
        #stDecoration {display:none;}
    </style>
""", unsafe_allow_html=True)

conf = config.Config()

# Titulo de la pagina
st.subheader("Revisar Documentos Resumidos", divider="violet")
#st.sidebar("Select a page")
st.sidebar.header("Páginas del sitio")
st.sidebar.subheader("2. Revisar documentos cargados")



dfcx_widget = """<script src="https://www.gstatic.com/dialogflow-console/fast/df-messenger/prod/v1/df-messenger.js"></script>
    <df-messenger
    project-id="genai-pdf-demos"
    agent-id="259c4f31-9c9b-4c3b-ad40-e33636f3514b"
    language-code="en">
    <df-messenger-chat-bubble
    chat-title="InversIA"  bot-writing-image="https://www.gstatic.com/lamda/images/sparkle_resting_v2_1ff6f6a71f2d298b1a31.gif">
    </df-messenger-chat-bubble>
    </df-messenger>
    <style>
    df-messenger {
        z-index: 999;
        position: fixed;
        bottom: 16px;
        right: 16px;
        --df-messenger-primary-color:#721f9c;
        --df-messenger-chip-border-color:#0041C2;
    }
    </style>"""
html(dfcx_widget, height=600, width=350)