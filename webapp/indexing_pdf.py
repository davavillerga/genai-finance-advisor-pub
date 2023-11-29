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

import os
#import CustomVertexAIEmbeddings
from utils.matching_engine_utils import MatchingEngineUtils
from utils.matching_engine import MatchingEngine
#from utils.matching_engine_utils import CustomVertexAIEmbeddings
import time
from typing import List

import config
import numpy as np
#import vertexai
import persistence_pdf 


#Langchain
from langchain.llms import VertexAI
from langchain.document_loaders import GCSDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Vertex AI
from google.cloud import aiplatform

import uuid
import json


conf = config.Config()

from pydantic import BaseModel
from langchain.embeddings import VertexAIEmbeddings

# Utility functions for Embeddings API with rate limiting
def rate_limit(max_per_minute):
    period = 60 / max_per_minute
    print("Waiting")
    while True:
        before = time.time()
        yield
        after = time.time()
        elapsed = after - before
        sleep_time = max(0, period - elapsed)
        if sleep_time > 0:
            print(".", end="")
            time.sleep(sleep_time)


class CustomVertexAIEmbeddings(VertexAIEmbeddings):
    requests_per_minute: int
    num_instances_per_batch: int

    # Overriding embed_documents method
    def embed_documents(self, texts: List[str]):
        limiter = rate_limit(self.requests_per_minute)
        results = []
        docs = list(texts)

        while docs:
            # Working in batches because the API accepts maximum 5
            # documents per request to get embeddings
            head, docs = (
                docs[: self.num_instances_per_batch],
                docs[self.num_instances_per_batch :],
            )
            chunk = self.client.get_embeddings(head)
            results.extend(chunk)
            next(limiter)

        return [r.values for r in results]


# Text model instance integrated with langChain
llm = VertexAI(
    model_name=conf.MODEL_NAME,
    max_output_tokens=1024,
    temperature=0.2,
    top_p=0.8,
    top_k=40,
    verbose=True,
)



def initialize_index():
    # dummy embedding
    init_embedding = {"id": str(uuid.uuid4()), "embedding": list(np.zeros(conf.ME_DIMENSIONS))}

    # dump embedding to a local file
    with open("embeddings_0.json", "w") as f:
        json.dump(init_embedding, f)
        
    # write embedding to Cloud Storage
    #! set -x && gsutil cp embeddings_0.json gs://{ME_EMBEDDING_DIR}/init_index/embeddings_0.json
    persistence_pdf.create_bucket_gcs(bucket_gcs=conf.ME_EMBEDDING_DIR, bucket_region=conf.ME_REGION)
    persistence_pdf.upload_pdf_gcs(bucket_gcs=conf.ME_EMBEDDING_DIR, source_file_path="embeddings_0.json", destination_gcs_name='init_index/embeddings_0.json')

# Crear un index nuevo en Matching Engine y desplegarlo en un Endpoint, este paso puede demorar 1 hora
def crear_index():
    mengine = MatchingEngineUtils(conf.PROJECT_ID, conf.ME_REGION, conf.ME_INDEX_NAME)
    index = mengine.create_index(
        embedding_gcs_uri = f"gs://{conf.ME_EMBEDDING_DIR}/init_index",
        dimensions = conf.ME_DIMENSIONS,
        index_update_method = "streaming",
        index_algorithm = "tree-ah",
    )
    if index:
        print(index.name)


    # Desplegar index en un Endpoint
    index_endpoint = mengine.deploy_index()
    if index_endpoint:
        print(f"Index endpoint resource name: {index_endpoint.name}")
        print(
            f"Index endpoint public domain name: {index_endpoint.public_endpoint_domain_name}"
        )
        print("Deployed indexes on the index endpoint:")
        for d in index_endpoint.deployed_indexes:
            print(f"    {d.id}")



# Cargar documentos PDF a un index de forma bulk, todos los docs de un bucket
def bulk_index_documents_ingest():
    # Ingestar archivos PDF an índice 
    GCS_BUCKET_DOCS = f"{conf.PROJECT_ID}-documents"
    folder_prefix = "documents/vectorsearch-original-pdfs/"



    print(f"Processing documents from {GCS_BUCKET_DOCS}")
    loader = GCSDirectoryLoader(
        project_name = conf.PROJECT_ID, bucket = GCS_BUCKET_DOCS, prefix=folder_prefix
    )
    documents = loader.load()


    # {PROJECT_ID}-documents/documents/google-research-pdfs/file.pdf
    # folder_prefix= documents/google-research-pdfs/
    # !gsutil rsync -r gs://github-repo/documents/google-research-pdfs/ gs://PROJECT_ID-documents/$folder_prefix
    # gs://PROJECT_ID-documents/documents/google-research-pdfs/file.pdf
    # ['gs://PROJECT_ID-documents', 'documents', 'google-research-pdfs', 'file.pdf'][4:-1]

    # Add document name and source to the metadata
    for document in documents:
        doc_md = document.metadata
        document_name = doc_md["source"].split("/")[-1]
        # derive doc source from Document loader
        doc_source_prefix = "/".join(GCS_BUCKET_DOCS.split("/")[:3])
        doc_source_suffix = "/".join(doc_md["source"].split("/")[4:-1])
        source = f"{doc_source_prefix}/{doc_source_suffix}"
        document.metadata = {"source": source, "document_name": document_name}

    print(f"# of documents loaded (pre-chunking) = {len(documents)}")

    print(f"Document 1 metadada: {documents[0].metadata}")

    # Separar los documentos en chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
    )
    doc_splits = text_splitter.split_documents(documents)

    # Add chunk number to metadata
    for idx, split in enumerate(doc_splits):
        split.metadata["chunk"] = idx

    print(f"# of documents = {len(doc_splits)}")

    mengine = MatchingEngineUtils(conf.PROJECT_ID, conf.ME_REGION, conf.ME_INDEX_NAME)
    ME_INDEX_ID, ME_INDEX_ENDPOINT_ID = mengine.get_index_and_endpoint()
    #ME_INDEX_ID = conf.ME_INDEX_ID 
    #ME_INDEX_ENDPOINT_ID = conf.ME_INDEX_ENDPOINT_ID

    print(f"ME_INDEX_ID={ME_INDEX_ID}")
    print(f"ME_INDEX_ENDPOINT_ID={ME_INDEX_ENDPOINT_ID}")

    #print(f"Authenticated as: {os.environ['GOOGLE_APPLICATION_CREDENTIALS']}")

    # Embeddings API integrated with langChain

    EMBEDDING_QPM = 100
    EMBEDDING_NUM_BATCH = 5
    embeddings = CustomVertexAIEmbeddings(
        requests_per_minute=EMBEDDING_QPM,
        num_instances_per_batch=EMBEDDING_NUM_BATCH,
    )


    # initialize vector store
    me = MatchingEngine.from_components(
        project_id = conf.PROJECT_ID,
        region = conf.ME_REGION,
        gcs_bucket_name = f"gs://{conf.ME_EMBEDDING_DIR}".split("/")[2],
        #gcs_bucket_name = f"gs://{conf.ME_EMBEDDING_DIR}".split("/")[1],
        embedding = embeddings,
        index_id = ME_INDEX_ID,
        endpoint_id = ME_INDEX_ENDPOINT_ID
        #credentials_path = os.environ["GOOGLE_APPLICATION_CREDENTIALS"],
        #credentials_path = os.environ["GOOGLE_APPLICATION_CREDENTIALS"],
    )

    # Store docs as embeddings in Matching Engine index
    # It may take a while since API is rate limited
    texts = [doc.page_content for doc in doc_splits]
    print(f"text variable contains: {texts[1]}")
    
    metadatas = [
        [
            {"namespace": "source", "allow_list": [doc.metadata["source"]]},
            {"namespace": "document_name", "allow_list": [doc.metadata["document_name"]]},
            {"namespace": "chunk", "allow_list": [str(doc.metadata["chunk"])]},
        ]
        for doc in doc_splits
    ]

    print(f"metadatas variable contains: {metadatas[0]}")

    # Este paso almacena los embeddings en el Vector Store, puede tomar un tiempo
    doc_ids = me.add_texts(texts=texts, metadatas=metadatas)

    # Pruebas de que se cargaron los docs y esta funcionando 
    respuesta = me.similarity_search("What is China's role in the global economy landscape after the pandemic?", k=2)
    


if __name__ == '__main__':
    #initialize_index()
    #crear_index()
    bulk_index_documents_ingest()