import json

from grocery60_be import settings
from google.cloud import pubsub_v1


def send_email_topic(email):
    publisher = pubsub_v1.PublisherClient()
    # The `topic_path` method creates a fully qualified identifier
    # in the form `projects/{project_id}/topics/{topic_id}`
    topic_path = publisher.topic_path(settings.PROJECT, 'email')

    data = vars(email)
    print('data', data )

    # Data must be a bytestring
    # using encode() + dumps() to convert to bytes
    data_bytes = json.dumps(data).encode('utf-8')
    # When you publish a message, the client returns a future.
    future = publisher.publish(topic_path, data=data_bytes)
    print(future.result())

    print("Published messages.")
