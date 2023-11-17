import boto3
import json
import os
from datetime import datetime
from botocore.exceptions import ClientError
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import base64
import inflection


REGION = 'us-east-1'
HOST = 'search-demo-photos-66psilnxccef5kzoj2imqouqki.us-east-1.es.amazonaws.com'
INDEX = 'photos'

def lambda_handler(event, context):
    rekognition = boto3.client('rekognition')
    s3 = boto3.client('s3')

    # print("event: ", event)
        
    # Get bucket name and object key from the S3 event
    bucket = event['Records'][0]['s3']['bucket']['name']
    object_key = event['Records'][0]['s3']['object']['key']


    # # Get the image object from S3
    s3_object = s3.get_object(Bucket=bucket, Key=object_key)
    # # Read the object data as a string
    image_data_url = s3_object['Body'].read().decode('utf-8')
    # # Extract the base64-encoded image data from the Data URL
    base64_image_data = image_data_url.split("base64,")[1]
    # # Decode the base64-encoded image
    image_data_bytes = base64.b64decode(base64_image_data)
    # # Detect labels using Rekognition with the image byte array
    response = rekognition.detect_labels(Image={'Bytes': image_data_bytes})


    # # Detect labels using Rekognition
    # response = rekognition.detect_labels(
    #     Image={
    #         'S3Object': {
    #             'Bucket': bucket,
    #             'Name': object_key
    #         }
    #     }
    #     # MaxLabels=10
    # )

    # Extract labels
    # labels = [label['Name'] for label in response['Labels']]
    labels = [inflection.singularize(label['Name']) for label in response['Labels']]

    # Get custom labels from S3 metadata if available
    metadata = s3.head_object(Bucket=bucket, Key=object_key)
    custom_labels = metadata.get('Metadata', {}).get('customlabels', '')
    # print("custom_labels:", custom_labels)
    if custom_labels:
        # labels.extend(custom_labels.split(','))
        singularized_custom_labels = [inflection.singularize(label) for label in custom_labels.split(',')]
        labels.extend(singularized_custom_labels)


    # Prepare the document to be indexed in OpenSearch
    document = {
        'objectKey': object_key,
        'bucket': bucket,
        'createdTimestamp': datetime.now().isoformat(),
        'labels': labels
    }
    
    try:
        client = OpenSearch(hosts=[{
            'host': HOST,
            'port': 443
        }],
                            http_auth=get_awsauth(REGION, 'es'),
                            use_ssl=True,
                            verify_certs=True,
                            connection_class=RequestsHttpConnection)
        
        if not client.indices.exists(index=INDEX):
            client.indices.create(index=INDEX, body={})
            
        index_response = client.index(index=INDEX, body=document)
        print("Document indexed:", document)
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                # Add other necessary CORS headers here
            },
            'body': json.dumps({
                'message': 'Upload successful',
                'objectKey': object_key,
                'bucket': bucket
            })
        }
    except Exception as e:
        print("An error occurred:", str(e))

def get_awsauth(region, service):
    cred = boto3.Session().get_credentials()
    return AWS4Auth(cred.access_key,
                    cred.secret_key,
                    region,
                    service,
                    session_token=cred.token)
