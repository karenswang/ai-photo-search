import boto3
import json
import os

# check out LF0 for reference 

lex = boto3.client('lexv2-runtime')
opensearch = boto3.client('opensearch')

def lambda_handler(event, context):
    query_from_user = event['queryStringParameters']['keyword']

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

    # Extract keywords from Lex response
    keywords_from_lex = lex_response.get('slots', {}).values()

    # Search in OpenSearch if keywords are present
    if keywords_from_lex:
        search_query = ' OR '.join(keywords_from_lex)
        search_response = opensearch.search(
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
        results = search_response['hits']['hits']
    else:
        results = []

    return {
        'statusCode': 200,
        'body': json.dumps({'results': results})
    }


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
