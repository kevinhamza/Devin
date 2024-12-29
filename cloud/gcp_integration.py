# cloud/gcp_integration.py
"""
Google Cloud Platform (GCP) Integration Module
==============================================

This module provides comprehensive integration with Google Cloud Platform (GCP),
allowing the project to interact seamlessly with various GCP services such as Compute Engine,
Cloud Storage, BigQuery, Pub/Sub, and more. 

The functionalities include service management, authentication, resource provisioning,
and usage monitoring.

Dependencies:
    - google-cloud-sdk
    - google-cloud-storage
    - google-cloud-bigquery
    - google-cloud-pubsub
"""

from google.cloud import storage, bigquery, pubsub_v1
import google.auth
import os

class GCPIntegration:
    def __init__(self, project_id=None, credentials_file=None):
        """
        Initialize the GCP integration module.

        Args:
            project_id (str): GCP project ID.
            credentials_file (str): Path to the GCP credentials JSON file.
        """
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID")
        self.credentials_file = credentials_file or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        self.credentials, self.default_project = google.auth.default()

        if self.credentials_file:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.credentials_file

    def initialize_storage_client(self):
        """
        Initialize the Google Cloud Storage client.
        
        Returns:
            google.cloud.storage.Client: The storage client.
        """
        return storage.Client(project=self.project_id, credentials=self.credentials)

    def initialize_bigquery_client(self):
        """
        Initialize the BigQuery client.
        
        Returns:
            google.cloud.bigquery.Client: The BigQuery client.
        """
        return bigquery.Client(project=self.project_id, credentials=self.credentials)

    def initialize_pubsub_client(self):
        """
        Initialize the Pub/Sub client.
        
        Returns:
            google.cloud.pubsub_v1.PublisherClient: The Pub/Sub publisher client.
            google.cloud.pubsub_v1.SubscriberClient: The Pub/Sub subscriber client.
        """
        publisher = pubsub_v1.PublisherClient(credentials=self.credentials)
        subscriber = pubsub_v1.SubscriberClient(credentials=self.credentials)
        return publisher, subscriber

    def upload_file_to_bucket(self, bucket_name, source_file_path, destination_blob_name):
        """
        Upload a file to a Google Cloud Storage bucket.

        Args:
            bucket_name (str): Name of the bucket.
            source_file_path (str): Path of the file to upload.
            destination_blob_name (str): Destination name for the file in the bucket.

        Returns:
            google.cloud.storage.blob.Blob: The uploaded blob object.
        """
        storage_client = self.initialize_storage_client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_path)
        return blob

    def query_bigquery(self, query):
        """
        Run a query on BigQuery.

        Args:
            query (str): SQL query string.

        Returns:
            google.cloud.bigquery.table.RowIterator: Query results.
        """
        bigquery_client = self.initialize_bigquery_client()
        query_job = bigquery_client.query(query)
        return query_job.result()

    def publish_message(self, topic_name, message):
        """
        Publish a message to a Pub/Sub topic.

        Args:
            topic_name (str): Name of the Pub/Sub topic.
            message (str): Message to publish.

        Returns:
            str: Message ID of the published message.
        """
        publisher, _ = self.initialize_pubsub_client()
        topic_path = publisher.topic_path(self.project_id, topic_name)
        future = publisher.publish(topic_path, message.encode("utf-8"))
        return future.result()

    def subscribe_to_topic(self, subscription_name, callback):
        """
        Subscribe to a Pub/Sub topic.

        Args:
            subscription_name (str): Name of the subscription.
            callback (function): Callback function to handle incoming messages.
        """
        _, subscriber = self.initialize_pubsub_client()
        subscription_path = subscriber.subscription_path(self.project_id, subscription_name)
        subscriber.subscribe(subscription_path, callback=callback)

# Example Usage:
if __name__ == "__main__":
    gcp = GCPIntegration(project_id="your_project_id", credentials_file="path/to/credentials.json")
    # Example of uploading a file to a bucket:
    # gcp.upload_file_to_bucket("your_bucket_name", "local_file.txt", "remote_file.txt")

    # Example of running a query in BigQuery:
    # results = gcp.query_bigquery("SELECT * FROM your_dataset.your_table LIMIT 10")
    # for row in results:
    #     print(row)

    # Example of publishing a message to Pub/Sub:
    # message_id = gcp.publish_message("your_topic_name", "Hello, World!")
    # print("Message published with ID:", message_id)
