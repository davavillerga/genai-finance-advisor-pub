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

import warnings
from pathlib import Path as p

import pandas as pd
from langchain.prompts import PromptTemplate
from langchain.chains.summarize import load_summarize_chain
from langchain.document_loaders import PyPDFLoader
from langchain.llms import VertexAI
from google.cloud import storage

import vertexai
import streamlit as st
import os
import tempfile
import datetime
from PIL import Image
from webapp.logo import add_logo

import config
from summarize_pdf import summarize_doc
import persistence_pdf
import discovery_engine_datastore

warnings.filterwarnings("ignore")


#print("App authenticated to GCP using the SA Key: {}".format(os.environ["GOOGLE_APPLICATION_CREDENTIALS"]))


conf = config.Config()
print("Project ID: {}".format(conf.PROJECT_ID))
print("Region: {}".format(conf.REGION))
print("Model Name: {}".format(conf.MODEL_NAME))


st.set_page_config(
    page_title="Asesor Financiero",
    page_icon=":bar_chart:",
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



image2 = Image.open(f"webapp/{conf.COMPANY_LOGO}")
st.image(image2, width=200)


st.title("Cargar Análisis Financiero para resumir")
#st.sidebar.header()
st.sidebar.subheader("1. Cargador de Documentos")
add_logo()
    #image = Image.open(f"webapp/{conf.COMPANY_LOGO}")
    #st.image(image, width=200)


st.header('Generador de resumenes de PDFs con Google GenAI y LangChain', divider="violet")


# PDF Uploadger widget
source_doc = st.file_uploader("Subir documento para resumir", type="pdf", accept_multiple_files=False)

if st.button("Resumir Documento"):
    # Validar inputs
    if not source_doc:
        st.write(f"Por favor cargue el archivo a resumir.")
    else:
        try:
            vertexai.init(project=conf.PROJECT_ID, location=conf.REGION)
            
            # Save uploaded file temporarily to disk, load and split the file into pages, delete temp file
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:

                # Cargar el PDF dividirlo en páginas
                tmp_file.write(source_doc.read())
                loader = PyPDFLoader(tmp_file.name)
                pages = loader.load_and_split()
                gcs_doc_id = F'{source_doc.name[:-4]}_{datetime.datetime.now()}.pdf'

                # Antes de borrar el archivo temporal, persisto el PDF original en Cloud Storage
                persistence_pdf.upload_pdf_gcs(bucket_gcs=conf.BUCKET_NAME, 
                                           source_file_path=tmp_file.name, 
                                           destination_gcs_name=gcs_doc_id)
                
                
                #print("Contenido de la pag. 2: {} ".format(pages[2].page_content))

                #Enviar el contenido de las páginas del doc al modelo para resumirlos
                summary = summarize_doc(project=conf.PROJECT_ID,
                                        location=conf.REGION, 
                                        vertex_model=conf.MODEL_NAME, 
                                        pages=pages)
                
                # Mostrar el resumen general del documento
                st.write(summary)                
                
                # Creo el dataframe que se enviará a BigQuery y que contiene el resumen de todo el documento
                doc_uri = F'gs://{conf.BUCKET_NAME}/{gcs_doc_id}'
                document_summary_df = pd.DataFrame({'document_id':[gcs_doc_id],
                                                    'document_name': [source_doc.name],
                                                    'document_gcs_uri': [doc_uri],
                                                    'document_llm_summary': [summary]
                                                    })
                #print(document_summary_df)

                # Persistir el resumen general del documento en la tabla correspondiente en BigQuery
                persistence_pdf.insert_doc_summary_bq(project=conf.PROJECT_ID, 
                                                      table_id=conf.DOCUMENTS_BQ_TABLE_ID, 
                                                      pandas_dataframe=document_summary_df)
                
                # Actualizar el índice del Data Store de Gen App Builder para que el agente conversacional esté al día con el nuevo doc:
                discovery_engine_datastore.import_documents_incremental(project_id=conf.PROJECT_ID, 
                                                                        location='global', 
                                                                        data_store_id=conf.DATA_STORE_ID, 
                                                                        gcs_uri=doc_uri)

                #Finalmente borro el archivo temporal
                os.remove(tmp_file.name)

        except Exception as e:
            st.write(f"An error occurred: {e}")
     