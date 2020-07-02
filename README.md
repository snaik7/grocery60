# grocery60
TLDR 
Grocery 60 app is deployed in Cloud Run on GCP

Set default project
gcloud config set project my-project

To make this the default region, run `gcloud config set run/region us-central1`.

Go to grocery60_be dir and run command to start the project

pipenv run python manage.py runserver

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

Postman Collection for API
https://www.getpostman.com/collections/b691809e7a7d9c5ba1a0

Hosted App : https://grocery60-be-b2yd4bi7eq-uc.a.run.app



Introduction
Grocery 60 uses Cloud Run managed compute platform that enables you to run stateless containers that are invocable via HTTP requests. Cloud Run is serverless: it abstracts away all infrastructure management, so you can focus on what matters most — building Grocery 60 applications.
It also natively interfaces with many other parts of the Google Cloud ecosystem, including Cloud SQL for managed databases, Cloud Storage for unified object storage, and Secret Manager for managing secrets.
Perform setup and requirements
First install the Google Cloud SDK, initialize it, and run core gcloud commands from the command-line.
https://cloud.google.com/sdk/docs/quickstart-macos

Perform Grocery60 project setup in GCP
https://codelabs.developers.google.com/codelabs/cloud-run-django/index.html?index=..%2F..index#1
Enable Cloud API
https://codelabs.developers.google.com/codelabs/cloud-run-django/index.html?index=..%2F..index#2
Clone repository
git clone git@github.com:snaik7/grocery60.git and you'll now have a folder called grocery60 which will contain a number of files, including a settings.py.
grocery60/
├── Dockerfile
├── Pipfile
├── Pipfile.lock
├── README.md
├── cloudmigrate.yaml
├── grocery60_be
│   ├── __init__.py
│   ├── __pycache__
│   │   ├── __init__.cpython-37.pyc
│   │   └── settings.cpython-37.pyc
│   ├── asgi.py
│   ├── error.py
│   ├── local_settings.py
│   ├── middleware.py
│   ├── migrations
│   │   ├── 0001_createsuperuser.py
│   │   └── __init__.py
│   ├── models.py
│   ├── serializers.py
│   ├── settings.py
│   ├── urls.py
│   ├── views.py
│   ├── viewsets.py
│   └── wsgi.py
├── manage.py
└── requirements.txt
Create the backing services
You'll now create your backing services: a Cloud SQL database, a Cloud Storage bucket, and a number of Secret Manager values.
Securing the values of the passwords used in deployment is important to the security of any project, and ensures that no one accidentally puts passwords where they don't belong (for example, directly in settings files, or typed directly into your terminal where they could be retrieved from history.)
First, Run the following command in Cloud Shell to confirm that you are authenticated:
gcloud auth list
 
Second, set two base environment variables, one for the project ID:
PROJECT_ID=$(gcloud config get-value core/project)
And one for the region:
REGION=us-central1
 
Create the database
Now, create a Cloud SQL instance, our instance name is grocery60. 
gcloud sql instances create grocery60 --project $PROJECT_ID \
  --database-version POSTGRES_11 --tier db-f1-micro --region $REGION
This operation may take a few minutes to complete.
Then in that Grocery60  instance, create a database. Fortunately, we are using database name same as instance name. Don’t get confused here.
gcloud sql databases create grocery60 --instance grocery60
Then in that same instance, create a user: First create password for the user. 
DJPASS="$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 30 | head -n 1)"
gcloud sql users create djuser --instance grocery60 --password $DJPASS
Create the storage bucket
Finally, create a Cloud Storage bucket (noting the name must be globally unique):
GS_BUCKET_NAME=${PROJECT_ID}-media
 
gsutil mb -l ${REGION} gs://${GS_BUCKET_NAME}
Store configuration as secret
Having set up the backing services, you'll now store these values in a file protected using Secret Manager.
Secret Manager allows you to store, manage, and access secrets as binary blobs or text strings. It works well for storing configuration information such as database passwords, API keys, or TLS certificates needed by an application at runtime.
First, create a file with the values for the database connection string, media bucket, and a secret key for Django (used for cryptographic signing of sessions and tokens):
 
 
DATABASE_URL=\"postgres://djuser:${DJPASS}@//cloudsql/${PROJECT_ID}:${REGION}:myinstance/mydatabase\" > .env
 
DATABASE_URL=\"postgres://djuser:${DJPASS}@//cloudsql/${PROJECT_ID}:${REGION}:grocery60/grocery60\" > .env
 
echo GS_BUCKET_NAME=\"${GS_BUCKET_NAME}\" >> .env
 
echo SECRET_KEY=\"$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 50 | head -n 1)\" >> .env
Then, create a secret called django_settings, using that file as the secret:
gcloud secrets create django_settings --replication-policy automatic
 
gcloud secrets versions add django_settings --data-file .env
Allow Cloud Run access to access this secret:
export PROJECTNUM=$(gcloud projects describe ${PROJECT_ID} --format 'value(projectNumber)')
export CLOUDRUN=${PROJECTNUM}-compute@developer.gserviceaccount.com
 
gcloud secrets add-iam-policy-binding django_settings \
  --member serviceAccount:${CLOUDRUN} --role roles/secretmanager.secretAccessor
Confirm the secret has been created by listing the secrets:
gcloud secrets list
After confirming the secret has been created, remove the local file:
rm .env
 
Configure your project
Given the backing services you just created, you'll need to understand some configuration changes applied to the  project to suit. This will include using django-environ to use environment variables as your configuration settings, which you'll seed with the values you defined as secrets.
Take the time to note the commentary added about each configuration. Any sections without comments are directly taken from the templated settings.py file without modification.
Finally, verify a file called requirements.txt in the top level of your project (where manage.py sits) with the various packages.
 
 Containerize app and upload it to Container Registry
Container Registry is a private container image registry that runs on Google Cloud. You'll use it to store your containerized project.
To containerize the grocery60 project, we have created a file named Dockerfile in the top level of your project (in the same directory as manage.py).
 
Now, build your container image using Cloud Build, by running the following command from the directory containing the Dockerfile:
gcloud builds submit --tag gcr.io/$PROJECT_ID/django-cloudrun
 
Once pushed to the registry, you'll see a SUCCESS message containing the image name. The image is stored in Container Registry and can be re-used if desired.
You can list all the container images associated with your current project using this command:
gcloud container images list
 
Run the Django migration steps

We don't use Django migrate to create databases. However, we have pre build scripts for the grocery60 database.

You will also need to run createsuperuser to create an administrator account to log into the Django admin.
Create your Django superuser
To create the superuser, you're going to use a data migration.
Now back in the terminal, create the admin_password as within Secret Manager, and only allow it to be seen by Cloud Build:
gcloud secrets create admin_password --replication-policy automatic

admin_password="$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 30 | head -n 1)"

echo -n "${admin_password}" | gcloud secrets versions add admin_password --data-file=-

export PROJECTNUM=$(gcloud projects describe ${PROJECT_ID} --format 'value(projectNumber)')
export CLOUDBUILD=${PROJECTNUM}@cloudbuild.gserviceaccount.com

gcloud secrets add-iam-policy-binding admin_password \
  --member serviceAccount:${CLOUDBUILD} --role roles/secretmanager.secretAccessor

Deploy to Cloud Run
With the backing services created and populated, you can now create the Cloud Run service to access them.
The initial deployment of your containerized application to Cloud Run is created using the following command. Here, we are using image grocery60-be from Google Cloud Registry and deploying an application with name grocery60-be.
gcloud run deploy grocery60-be --platform managed --region $REGION \
  --image gcr.io/$PROJECT_ID/grocery60-be \
  --add-cloudsql-instances ${PROJECT_ID}:${REGION}:grocery60 \
  --allow-unauthenticated
 
Wait a few moments until the deployment is complete. On success, the command line displays the service URL:
Service [grocery60-be] revision [grocery60-...] has been deployed
and is serving traffic at https://grocery60-...-uc.a.run.app
You can also retrieve the service URL with this command:
gcloud run services describe grocery60 \
  --platform managed \
  --region $REGION  \
  --format "value(status.url)"
 
You can now visit your deployed container by opening this URL in a web browser:
You can also log into the Django admin interface (add /admin to the URL) with the username "admin" and the admin password, which you can retrieve using the following command:
gcloud secrets versions access latest --secret admin_password
 
Deploying again
If you want to make any changes to your Django project, you'll need to build your image again:
gcloud builds submit --tag gcr.io/$PROJECT_ID/grocery60-be
Finally, re-deploy:
gcloud run deploy grocery60-be --platform managed --region $REGION \
  --image gcr.io/$PROJECT_ID/grocery60-be
 
 
 
 
 






