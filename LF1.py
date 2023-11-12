import boto3
import json
import os
from datetime import datetime
from botocore.exceptions import ClientError
import requests


def lambda_handler(event, context):
    rekognition = boto3.client('rekognition')
    s3 = boto3.client('s3')
    opensearch = boto3.client('es') # es = boto3.client('es')
    
    print("event: ", event)
        
    # Get bucket name and object key from the S3 event
    bucket = event['Records'][0]['s3']['bucket']['name']
    object_key = event['Records'][0]['s3']['object']['key']

    # Detect labels using Rekognition
    response = rekognition.detect_labels(
        Image={
            'S3Object': {
                'Bucket': bucket,
                'Name': object_key
            }
        }
        # MaxLabels=10
    )

    # Extract labels
    labels = [label['Name'] for label in response['Labels']]

    # Get custom labels from S3 metadata if available
    metadata = s3.head_object(Bucket=bucket, Key=object_key)
    custom_labels = metadata.get('Metadata', {}).get('customlabels', '')
    # print("custom_labels:", custom_labels)
    if custom_labels:
        labels.extend(custom_labels.split(','))

    # Prepare the document to be indexed in OpenSearch
    document = {
        'objectKey': object_key,
        'bucket': bucket,
        'createdTimestamp': datetime.now().isoformat(),
        'labels': labels
    }

    # # # Index the document in OpenSearch
    # index_response = opensearch.index(
    #     Index='photos',
    #     Body=json.dumps(document)
    # )
    # opensearch.index(index='photos', doc_type='_doc', body=document)
    
    
    # Index the document in OpenSearch Service (Amazon Elasticsearch)
    opensearch_endpoint = "https://search-photos-h5rkn7iyx5ntfplwz52f3bzf5q.us-east-1.es.amazonaws.com"
    index_name = "photos"
    
    bulk_request_body = json.dumps({"index": {"_index": index_name}}) + "\n"
    bulk_request_body += json.dumps(existing_document) + "\n"
    
    try:
        # Send the bulk index request to OpenSearch
        response = requests.post(
            f"{opensearch_endpoint}/{index_name}/_bulk",
            headers={"Content-Type": "application/json"},
            data=bulk_request_body
        )
        
    # Process the response
        if response.status_code == 200:
            result = json.loads(response.text)
            print("Bulk indexing of existing document successful:", result)
        else:
            print("Bulk indexing of existing document failed with status code:", response.status_code)
            print("Response content:", response.text)
    except Exception as e:
        print("An error occurred:", str(e))
        # Handle the error as needed


    # return {
    #     'statusCode': 200,
    #     'body': json.dumps(index_response)
    # }

# def lambda_handler(event, context):
#     for record in event['Records']:
#         bucket_name = record['s3']['bucket']['name']
#         object_key = record['s3']['object']['key']
        
#         try:
#             # Detect labels in the image using Rekognition
#             response = rekognition.detect_labels(
#                 Image={
#                     'S3Object': {
#                         'Bucket': bucket_name,
#                         'Name': object_key
#                     }
#                 },
#                 MaxLabels=10
#             )
#             labels = [label['Name'] for label in response['Labels']]

#             # Retrieve custom labels from S3 metadata
#             response = s3.head_object(Bucket=bucket_name, Key=object_key)
#             custom_labels = response['Metadata'].get('x-amz-meta-customlabels', '').split(',')

#             # Merge Rekognition labels and custom labels
#             all_labels = list(set(labels + custom_labels))

#             # Prepare the document to be indexed in OpenSearch
#             document = {
#                 'objectKey': object_key,
#                 'bucket': bucket_name,
#                 'createdTimestamp': datetime.now().isoformat(),
#                 'labels': all_labels
#             }

#             # Index the document in OpenSearch
#             es.index(index='photos', doc_type='_doc', body=json.dumps(document))

#         except ClientError as e:
#             print(f'Error processing object {object_key} from bucket {bucket_name}. Error: {e}')

#     return {
#         'statusCode': 200,
#         'body': json.dumps('Processing complete')
#     }