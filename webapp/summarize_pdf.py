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

"""
 Este modulo toma las paginas del PDF, realiza un resumen parcial de cada una, 
 y finalmente con cada resumen parcial, genera un resumen general de todo el documento.
"""

import warnings
from pathlib import Path as p

import pandas as pd
from langchain import PromptTemplate
from langchain.chains.summarize import load_summarize_chain
from langchain.document_loaders import PyPDFLoader
from langchain.llms import VertexAI

import vertexai




def summarize_doc(project, location, vertex_model, pages):
    """
    El método refine se trata de dividir el documento en piezas de texto llamadas chunks 
    (al igual que otros métodos de summarización de texto de grandes documentos), 
    pero a diferencia de otros métodos que procesan los chunks en paralelo haciendo un resumen de cada uno 
    mediante múltiples llamadas al LLM, para al final resumir todos esos resumenes 
    (potenialmente perdiendo algo del contexto por ese paralelismo ya que se hacen resúmenes independientes); 
    en el método Refine, se usa un prompt para realizar el resumen del primer chunk, y luego de forma serializada, 
    se le hacen llamadas consecutivas al LLM con otro prompt para hacer resúmenes de los nuevos chunks, 
    incorporando el resumen que ya se hizo, "refinando" el resumen total en cada iteración hasta que se resume todo el documento, 
    logrando así mantener algo del contexto. Este método tiene la desventaja de que como se ejecutan las llamadas de forma serial,
    no es tan paralelizable como otros métodos, ya cada llamada con el segundo prompt depende del resumen "refinado" de la iteración anterior
    """

    vertexai.init(project=project, location=location)

    question_prompt_template = """
                    Provide a summary of the following text.
                    TEXT: {text}
                    SUMMARY:
                    """

    question_prompt = PromptTemplate(
        template=question_prompt_template, input_variables=["text"]
    )

    refine_prompt_template = """
                Write a concise summary of the following text delimited by triple backquotes.
                Return your response in no more than 2 bullet points which covers the key points of the text.
                ```{text}```
                BULLET POINT SUMMARY:
                """

    refine_prompt = PromptTemplate(
        template=refine_prompt_template, input_variables=["text"]
    )

    vertex_llm_text = VertexAI(model_name=vertex_model)

    refine_chain = load_summarize_chain(
        vertex_llm_text,
        chain_type="refine",
        question_prompt=question_prompt,
        refine_prompt=refine_prompt,
        return_intermediate_steps=True,
    )


    # La funcion refine_chain() es la que llama al Modelo LLM y hace los resumenes (este paso puede tomar un tiempo)
    refine_outputs = refine_chain({"input_documents": pages})


    # Se crea un arreglo de los resumenes que se ha realizado para cada pagina del documento y se agregan a un diccionanio llamado final_refine_data[]. Luego se crea un Dataframe en Pandas a partir de este diccionario para visualizar el resumen de cada chunk (pagina del doc)
    final_refine_data = []
    for doc, out in zip(
        refine_outputs["input_documents"], refine_outputs["intermediate_steps"]
    ):
        output = {}
        output["file_name"] = p(doc.metadata["source"]).stem
        output["file_type"] = p(doc.metadata["source"]).suffix
        output["page_number"] = doc.metadata["page"]
        output["chunks"] = doc.page_content
        output["concise_summary"] = out
        final_refine_data.append(output)
    
    pdf_refine_summary = pd.DataFrame.from_dict(final_refine_data)
    pdf_refine_summary = pdf_refine_summary.sort_values(by=["file_name", "page_number"])  # sorting the dataframe by filename and page_number
    pdf_refine_summary.reset_index(inplace=True, drop=True)
    #pdf_refine_summary.head()


    summarized_text = ""

    for ind in pdf_refine_summary["concise_summary"]:
        summarized_text += ind
        
    # print(summarized_text)

    print("Total Character lenght of document summary: {}".format(len(summarized_text)))

    return summarized_text
