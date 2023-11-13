import boto3
import json
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

REGION = 'us-east-1'
HOST = 'search-photos-h5rkn7iyx5ntfplwz52f3bzf5q.us-east-1.es.amazonaws.com'
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
    
    # Combine keywords, filtering out empty ones
    keywords_from_lex = [keyword for keyword in [keyword1, keyword2] if keyword]
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
            'body': json.dumps({'error': str(e)})
        }
    
    return {
        'statusCode': 200,
        'body': json.dumps({'results': results})
    }
    
    
def query(keywords):
    search_query = ' OR '.join(keywords)

    client = OpenSearch(hosts=[{
        'host': HOST,
        'port': 443
    }],
                        http_auth=get_awsauth(REGION, 'es'),
                        use_ssl=True,
                        verify_certs=True,
                        connection_class=RequestsHttpConnection)

    search_response = client.search(
            Index='photos',
            Body={
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
        results.append(hit['_source'])

    return results
    
    
def get_awsauth(region, service):
    cred = boto3.Session().get_credentials()
    return AWS4Auth(cred.access_key,
                    cred.secret_key,
                    region,
                    service,
                    session_token=cred.token)


# import boto3
# import json
# from botocore.exceptions import ClientError

# def lambda_handler(event, context):
#     lex = boto3.client('lex-runtime')
#     es = boto3.client('es')

#     query = event.get('queryStringParameters', {}).get('q', '')

#     try:
#         # Send the query to Lex for processing
#         lex_response = lex.post_text(
#             botName='YourBotName', # Replace with your bot name
#             botAlias='YourBotAlias', # Replace with your bot alias
#             userId='user-id', # A unique ID for the user
#             inputText=query
#         )

#         # Extract keywords from Lex response (adapt based on your Lex setup)
#         keywords = lex_response.get('slots', {}).values()

#         # Search OpenSearch with the keywords
#         search_query = ' '.join(keywords)
#         es_response = es.search(
#             index='photos',
#             body={
#                 'query': {
#                     'match': {
#                         'labels': search_query
#                     }
#                 }
#             }
#         )

#         # Extract and format the search results
#         results = [hit['_source'] for hit in es_response['hits']['hits']]

#     except ClientError as e:
#         print(f'Error: {e}')
#         results = []

#     return {
#         'statusCode': 200,
#         'body': json.dumps({'results': results})
#     }


