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
 Este modulo maneja la persistencia tanto de los documentos PDF en GCS, como los resumenes parciales generados con PaLM
 para cada pagina, de cada documento que se haya subido a la app, asi como el resumen general de los documentos a BigQuery.
 Contiene tanto funciones para subir archivos a GCS e insertar resumenes de los documentos en BigQuery, 
 como funciones para descargar esos archivos desde GCS y obtener sus resumenes desde las correspondientes tablas en BigQuery
"""

from google.cloud import storage, bigquery
import pandas as pd


# Funcion que sube documento a Google Cloud Storage
def upload_pdf_gcs(bucket_gcs, source_file_path, destination_gcs_name):
    """Uploads a file to the bucket."""
    # The ID of your GCS bucket
    bucket_name = bucket_gcs
    # The path to your file to upload
    source_file_name = source_file_path
    # The ID of your GCS object
    destination_blob_name = destination_gcs_name

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    # Optional: set a generation-match precondition to avoid potential race conditions
    # and data corruptions. The request to upload is aborted if the object's
    # generation number does not match your precondition. For a destination
    # object that does not yet exist, set the if_generation_match precondition to 0.
    # If the destination object already exists in your bucket, set instead a
    # generation-match precondition using its generation number.
    generation_match_precondition = 0

    blob.upload_from_filename(source_file_name, if_generation_match=generation_match_precondition)

    print(
        f"File {source_file_name} uploaded to {destination_blob_name}."
    )


def list_pdf_gcs(bucket_gcs):
    """Lists all the blobs in the bucket."""
    bucket_name = bucket_gcs
    # List all the blobs in the bucket
    storage_client = storage.Client()
    blobs = storage_client.list_blobs(bucket_name)
    documents = []
    
    for blob in blobs:
        documents.append({"name": blob.name, "url": blob.public_url.split('/')[-1]})
        print("Name: {} , URL: {}".format(blob.name, blob.public_url.split('/')[-1]))
        
    return documents

# Funcion para descargar un archivo PDF desde Cloud Storage
def download_pdf_gcs(bucket_gcs, filename):
    
    # The ID of your GCS bucket
    bucket_name = bucket_gcs

    # The ID of your GCS object
    source_blob_name = filename

    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)

    # Construct a client side representation of a blob.
    # Note `Bucket.blob` differs from `Bucket.get_blob` as it doesn't retrieve
    # any content from Google Cloud Storage. As we don't need additional data,
    # using `Bucket.blob` is preferred here.
    blob = bucket.blob(source_blob_name)
    contents = blob.download_as_bytes()
    
    #print("Downloaded storage object {} from bucket {} as the following string: {}.".format(filename, bucket_name, contents))

    return contents


# Funcion que inserta en BigQuery el resumen de un documento cargado
def insert_doc_summary_bq(project, table_id, pandas_dataframe):
    print("Inserting data into BigQuery")

    # Create a pandas dataframe.
    df = pandas_dataframe

    # Create a BigQuery client.
    client = bigquery.Client()

    # Insert the dataframe into BigQuery.
    df.to_gbq(
        project_id = project,
        destination_table = table_id,
        if_exists='append'
    )

# Funcion que devuelve la lista de todos los resumenes de los documentos
def get_doc_summary_bq(table_id, doc_id):
    print("Getting data from BigQuery")
    client = bigquery.Client()

    sql = F'SELECT document_id, document_name, document_gcs_uri, document_llm_summary FROM `{table_id}` WHERE document_id = "{doc_id}"' 
    
    df = client.query(sql).to_dataframe()

    return df



# Funcion que devuelve la lista de todos los resumenes de los documentos
def get_all_summaries_bq(table_id):
    print("Getting data from BigQuery")
    client = bigquery.Client()

    sql = F'SELECT document_id, document_name, document_gcs_uri, document_llm_summary FROM `{table_id}`' 
    
    df = client.query(sql).to_dataframe()

    return df

# Funcion helper para crear un bucket en GCS
def create_bucket_gcs(bucket_gcs, bucket_region):
    """Creates a new bucket."""
    # The ID to give your GCS bucket
    # bucket_name = "your-new-bucket-name"

    storage_client = storage.Client()

    bucket = storage_client.create_bucket(bucket_gcs, location=bucket_region)

    print(f"Bucket {bucket.name} created")
