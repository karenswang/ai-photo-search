import boto3
from datetime import datetime
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

REGION = 'us-east-1'
HOST = 'search-photos-h5rkn7iyx5ntfplwz52f3bzf5q.us-east-1.es.amazonaws.com'
INDEX = 'photos'

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
    except Exception as e:
        print("An error occurred:", str(e))

def get_awsauth(region, service):
    cred = boto3.Session().get_credentials()
    return AWS4Auth(cred.access_key,
                    cred.secret_key,
                    region,
                    service,
                    session_token=cred.token)