# grocery60
Grocery 60 app is deployed in Cloud Run on GCP

Set default project
gcloud config set project my-project

To make this the default region, run `gcloud config set run/region us-central1`.

Create build after change
gcloud builds submit --tag gcr.io/$PROJECT_ID/grocery60-be

Deploy after change 
gcloud run deploy grocery60-be --platform managed --region $REGION \
  --image gcr.io/$PROJECT_ID/grocery60-be \
  --add-cloudsql-instances ${PROJECT_ID}:${REGION}:grocery60 \
  --allow-unauthenticated

Receive endpoint for service
gcloud run services describe grocery60-be \
  --platform managed \
  --region $REGION  \
  --format "value(status.url)"

URLS to API

Get Store

http://localhost:8000/store/

http://localhost:8000/store/1

http://localhost:8000/store/?zip=94526


Catalog

http://localhost:8000/catalog/

http://localhost:8000/catalog/?product_category=dairy&store_id=1



