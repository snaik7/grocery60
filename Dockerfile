# Use an official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.8-slim

ENV APP_HOME /app
WORKDIR $APP_HOME

# Install dependencies.
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy local code to the container image.
COPY . .


# uWSGI will listen on this port
EXPOSE 8000

# Service must listen to $PORT environment variable.
# This default value facilitates local development.
ENV PORT 8000

# reference doc - https://medium.com/@lhennessy/running-django-on-google-cloud-run-with-cloudsql-ac8141095b77
# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
#CMD python ./grocery60_be/manage.py runserver 0.0.0.0:$PORT
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 0 grocery60_be.wsgi:application