import boto3
import json
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import inflection

REGION = 'us-east-1'
HOST = 'search-demo-photos-66psilnxccef5kzoj2imqouqki.us-east-1.es.amazonaws.com'
INDEX = 'photos'

# check out LF0 for reference 

def lambda_handler(event, context):
    # query_from_user = event['queryStringParameters']['keyword']
    query_from_user = event['keyword'] # keyword here can be a sentence
    
    lex = boto3.client('lexv2-runtime')
    opensearch = boto3.client('opensearch')

    # Disambiguate the query using Amazon Lex
    # lex_response = lex.post_text(
    #     botName='YourLexBotName',
    #     botAlias='',
    #     userId='',
    #     inputText=query_from_user
    # )

    lex_response = lex.recognize_text(
        botId='WRDYKDEUOV',
        botAliasId='SLVZYGVSIQ',
        localeId='en_US',
        sessionId='testuser',
        text=query_from_user)

    print(lex_response)
    
    
    # Extract keywords from Lex response
    slots = lex_response.get('sessionState', {}).get('intent', {}).get('slots', {})
    # For Keyword1, which is mandatory
    keyword1 = slots.get('Keyword1', {}).get('value', {}).get('interpretedValue', '')
    # For optional Keyword2
    keyword2_slot = slots.get('Keyword2', {})
    if keyword2_slot and 'value' in keyword2_slot:
        keyword2 = keyword2_slot['value'].get('interpretedValue', '')
    else:
        keyword2 = ''
    
    # Combine keywords, filtering out empty ones and singularize them
    keywords_from_lex = [inflection.singularize(keyword) for keyword in [keyword1, keyword2] if keyword]
    print(keywords_from_lex)
    
    try:
        # Search in OpenSearch if keywords are present
        if keywords_from_lex:
            results = query(keywords_from_lex)
        else:
            results = []
    except Exception as e:
        print("An error occurred:", str(e))
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,keyword'
            },
            'body': json.dumps({'error': str(e)})
        }
    
    formatted_response = {"results": results}
    return {
        'statusCode': 200,
        'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET,OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,keyword'
            },
        'body': json.dumps(formatted_response)
    }

    
def query(keywords):
    search_query = ' AND '.join(keywords)

    client = OpenSearch(hosts=[{
        'host': HOST,
        'port': 443
    }],
                        http_auth=get_awsauth(REGION, 'es'),
                        use_ssl=True,
                        verify_certs=True,
                        connection_class=RequestsHttpConnection)

    search_response = client.search(
            index='photos',
            body={
                'query': {
                    'multi_match': {
                        'query': search_query,
                        'fields': ['labels']
                    }
                }
            }
        )

    print(search_response)

    hits = search_response['hits']['hits']
    results = []
    for hit in hits:
        source = hit['_source']
        bucket = source.get('bucket')
        objectKey = source.get('objectKey')
        
        # Return a pre-signed photo URL for frontend rendering
        # photo_url = f'https://{bucket}.s3.amazonaws.com/{objectKey}'
        s3_client = boto3.client('s3')
        presigned_url = s3_client.generate_presigned_url('get_object',
                                                 Params={'Bucket': bucket,
                                                         'Key': objectKey},
                                                 ExpiresIn=3600)  # URL expires in 1 hour

        photo_object = {
            "url": presigned_url,
            "labels": source.get('labels', [])
        }
        results.append(photo_object)

    return results
    
    
def get_awsauth(region, service):
    cred = boto3.Session().get_credentials()
    return AWS4Auth(cred.access_key,
                    cred.secret_key,
                    region,
                    service,
                    session_token=cred.token)
