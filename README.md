# grocery60

# Overview

Grocery 60 app is deployed in Cloud Run on GCP. The README file introduces the general approach for organizing this stuff and then explains how to install it, how to use the existing functionality
and how to extend it.

## Introduction

The goal is to have a zero to hero one-click setup that can be extended for specific purposes (e.g. work stuff) without touching the base. 

## Installation

Make sure git is installed:
Then, clone the repository and follow setup script:

```
$ git version
git version 2.25.0
```
Set default project
```
gcloud config set project my-project
```
To make this the default region, run 
```
gcloud config set run/region us-central1
```

Go to grocery60_be dir and run command to start the project
```
pipenv run python manage.py runserver
```
Create build after change
```
gcloud builds submit --tag gcr.io/$PROJECT_ID/grocery60-be
```

Deploy after change 
```
gcloud run deploy grocery60-be --platform managed --region $REGION \
  --image gcr.io/$PROJECT_ID/grocery60-be \
  --add-cloudsql-instances ${PROJECT_ID}:${REGION}:grocery60 \
  --allow-unauthenticated
```
Receive endpoint for service
```
gcloud run services describe grocery60-be \
  --platform managed \
  --region $REGION  \
  --format "value(status.url)"
 ```

 Hosted App : https://grocery60-be-b2yd4bi7eq-uc.a.run.app

## Usage

Postman Collection for API
https://www.getpostman.com/collections/b691809e7a7d9c5ba1a0

##Deployment

Read setup guide for more details  https://docs.google.com/document/d/1dODRtnbE1NpOdIMGnGwpap-sVouwTz9pjrxJCMp31Cs/edit#heading=h.bfe1hv37sxqb






 
 
 
 






