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

class Config(object):

    basedir = os.path.abspath(os.path.dirname(__file__))

    """ DEBUG = (os.getenv('DEBUG', 'False') == 'True') """
    DEBUG = True

    # Set the GOOGLE_APPLICATION_CREDENTIALS os environment variable
    # os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/..../key.json' # Point to your SA key, leave commented if using Cloud Run with the compute default Service Account 
    
    
    # Assets Management
    #ASSETS_ROOT = os.getenv('ASSETS_ROOT', '/static/assets')
    
    # Company specific information - Fill in with the name of a file of an image you have previously uploaded to the path /webapp/static/assets and the COMPANY_NAME should contain a string with the Company name
    COMPANY_LOGO = "cymbal_logo.png"
    GCP_LOGO = "google-cloud.webp"
    COMPANY_NAME = "Cymbal Investments"

    GOOGLE_GEN_AI_LOGO = "https://www.gstatic.com/lamda/images/sparkle_resting_v2_1ff6f6a71f2d298b1a31.gif"

    # GCP config constants
    # Project details:
    PROJECT_ID = ""  #YOUR_PROJECT_ID
    REGION = 'us-east1'
    ZONE = 'us-east1-b'
    BUCKET_NAME = "" #YOUR_BUCKET_NAME (not the URI)
    #FILE_NAME = "morgan_2023_investment.pdf"
    MODEL_NAME="text-bison@001"
    
    #The following tables need to exist in your project:
    BQ_DATASET_ID = F'{PROJECT_ID}.pdf_summarizer_data'
    DOCUMENTS_BQ_TABLE_ID = F'{PROJECT_ID}.pdf_summarizer_data.pdf-documents-summaries'
    PAGES_BQ_TABLE_ID = F'{PROJECT_ID}.pdf_summarizer_data.pdf-documents-pages-summaries'

    # Vertex AI Conversation & Search Datastore ID
    DATA_STORE_ID = ''  # The Data Store ID of the store you created in your project
    DFCX_AGENT = ''  # The published Dialogflow CX Agent ID

    # Vector Store constants:
    ME_REGION = "us-east1"
    ME_INDEX_NAME = f"{PROJECT_ID}-me-index"  
    ME_EMBEDDING_DIR = f"{PROJECT_ID}-me-bucket"  
    ME_DIMENSIONS = 768  # when using Vertex PaLM Embedding

    ME_INDEX_ID = '' # The Search Vector Store ID of the Matching Engine (Vector Search) you created in your project
    ME_INDEX_ENDPOINT_ID = '' # The Endpoint ID where the Matching Engine Vector Store is deployed