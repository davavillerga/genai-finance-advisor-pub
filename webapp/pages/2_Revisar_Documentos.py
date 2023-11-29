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
import os, tempfile
import base64
import persistence_pdf
import config
import matplotlib.pyplot as plt
import time
from langchain.document_loaders import PyPDFLoader
from wordcloud import WordCloud, STOPWORDS

from streamlit.components.v1 import html
from PIL import Image
from webapp.logo import add_logo

#from io import BytesIO


st.set_page_config(
    page_title="Asesor Financiero",
    page_icon="hello",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Quitar el botón Deploy de Streamlit
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

# Cargar el archivo de configuración
conf = config.Config()

image2 = Image.open(f"webapp/{conf.COMPANY_LOGO}")
st.image(image2, width=100)

# Titulo de la pagina
st.subheader("Revisar Documentos Resumidos", divider="violet")
add_logo()
#st.sidebar("Select a page")
#st.sidebar.header("Páginas del sitio")
#st.sidebar.subheader("2. Revisar documentos cargados")


#Definicion de las columnas del layout
col1, col2, col3 = st.columns([1,2,1], gap="small")

# Buscar los documentos ya cargados y sus resumenes en BigQuery y GCS

# Buscar Documentos disponibles en GCS
docs = persistence_pdf.list_pdf_gcs(conf.BUCKET_NAME)
docs_list = []
for doc in docs:
    docs_list.append(doc["name"])
docs_tuple = tuple(docs_list)


# Columna que muestra el DropDown de los documentos disponibles, junto con el Dataframe con todos los resumenes
with col1:
    option = st.selectbox('Seleccione el documento a revisar en detalle:', docs_tuple)

    #st.write('You selected:', option)

    # Descargar el documento original desde GCS a almacenamiento temporal:
    source_doc = persistence_pdf.download_pdf_gcs(bucket_gcs=conf.BUCKET_NAME, filename=option)

    # Consultar y cargar desde BigQuery en un Dataframe el resumen de todos los documentos
    all_docs_summaries_df = persistence_pdf.get_all_summaries_bq(table_id=conf.DOCUMENTS_BQ_TABLE_ID)

    # Consultar y cargar desde BigQuery en un Dataframe el resumen del documento seleccionado en el Dropdown
    doc_summary_df = persistence_pdf.get_doc_summary_bq(table_id=conf.DOCUMENTS_BQ_TABLE_ID, doc_id=option)
    #print(doc_summary_df)

    st.write("Resumenes de Documentos cargados:")
    all_docs_summaries_df.columns = ['document_id','Documento','uri','Resumen']
    st.write(all_docs_summaries_df['Resumen'])

    # Nube de palabras
    st.write("Nube de Palabras:")
    texto=doc_summary_df.loc[0,'document_llm_summary']
    st.set_option('deprecation.showPyplotGlobalUse', False)
    if texto:
        w = WordCloud().generate(texto)
        plt.imshow(w, interpolation='bilinear')
        plt.axis("off")
        st.pyplot()
    

# Columa central en que se muestra el resumen del documento seleccionado en el dropdown
with col2:
    progress_text = "Cargando resumen del documento..."
    my_bar = st.progress(0, text=progress_text)

    for percent_complete in range(100):
        time.sleep(0.01)
        my_bar.progress(percent_complete + 1, text=progress_text)
    time.sleep(1)
    my_bar.empty()

    st.subheader(F"Resumen del documento: :blue[{doc_summary_df.loc[0,'document_name']}]")
    
    expander = st.expander("Resumen del documento")
    expander.write(doc_summary_df.loc[0,'document_llm_summary'])

    # Display original PDF
    #print(source_doc)
    #print(tmp_file.name)
    #base64_pdf = base64.b64encode(source_doc.read()).decode('utf-8')
    #pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="800" height="800" type="application/pdf"></iframe>'
    #st.markdown(pdf_display, unsafe_allow_html=True)
    #os.remove(tmp_file.name)


# No utilizado Columna que muestra el documento PDF original descargado desde GCS
    # with tempfile.NamedTemporaryFile(delete=False, mode='wb') as tmp_file:
    #         #print(source_doc)
    #         tmp_file.write(source_doc)
    #         print(tmp_file.name)
    #         #base64_pdf = base64.b64encode(tmp_file.read()).decode('utf-8')
    #         pdf_display = f'<iframe src="data:application/pdf;base64,{tmp_file.name}" width="800" height="800" type="application/pdf"></iframe>'
    #         st.markdown(pdf_display, unsafe_allow_html=True)
    #         #os.remove(tmp_file.name)
    
# Columna que muestra la nube de palabras del documento seleccionado en el Dropdown
with col3:
    st.write("Pregunte al asistente:")    
    # Pintar widget DFCX:


    dfcx_widget = f"""<script src="https://www.gstatic.com/dialogflow-console/fast/df-messenger/prod/v1/df-messenger.js"></script>
    <df-messenger
    project-id="{conf.PROJECT_ID}"
    agent-id="{conf.DFCX_AGENT}"
    language-code="en">
    <df-messenger-chat-bubble
    chat-title="InversIA"  bot-writing-image="https://www.gstatic.com/lamda/images/sparkle_resting_v2_1ff6f6a71f2d298b1a31.gif">
    </df-messenger-chat-bubble>
    </df-messenger>
    <style>
    df-messenger {{
        z-index: 999;
        position: fixed;
        bottom: 16px;
        right: 16px;
        --df-messenger-primary-color:#721f9c;
        --df-messenger-chip-border-color:#0041C2;
    }}
    </style>"""
    html(dfcx_widget, height=600, width=350)



