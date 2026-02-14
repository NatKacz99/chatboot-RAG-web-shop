import boto3
import json
import numpy as np

BUCKET_NAME = "rag-shop-vectors"
bedrock = boto3.client("bedrock-runtime")
s3 = boto3.client("s3")

def embed_text(text: str) -> list:
    response = bedrock.invoke_model(
        modelId="amazon.titan-embed-text-v2:0",
        body = json.dumps({
            "inputText": text
        })
    )
    body_bytes = response["body"].read()
    response_data = json.loads(body_bytes)
    return response_data["embedding"]

def cosine_similarity(vector1, vector2):
    """Calculates the cosine similarity between two vectors"""
    return np.dot(vector1, vector2) / (np.linalg.norm(vector1) * np.linalg.norm(vector2))

def search_similar_chunks(question_embedding: list, top_k: int = 3) -> list:
    response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix="vectors/")

    if 'Contents' not in response:
        return []
    
    similarities = []

    for obj in response["Contents"]:
        file_obj = s3.get_object(Bucket=BUCKET_NAME, Key=obj['Key'])
        file_content = json.loads(file_obj['Body'].read())

        similarity = cosine_similarity(question_embedding, file_content['embedding'])

        similarities.append({
            'content': file_content['content'],
            'similarity': similarity
        })

    similarities.sort(key=lambda x: x['similarity'], reverse=True)

    return [item['content'] for item in similarities[:top_k]]

def generate_response_with_claude(question: str, docs: list) -> str:
    context = "\n\n".join([f"Fragment {i+1}:\n{doc}" for i, doc in enumerate(docs)])

    prompt = f"""You are a helpful shop assistant.
    <knowledge_base>
    {context}
    </knowledge_base>

    <question>
    {question}
    </question>

    Rules:
    1. Answer ONLY based on information from the knowledge base.
    2. If the information is not in the database, 
    say "Sorry, I don't have this information in the knowledge base".
    3. Respond in Polish, concisely and professionally
    4. If your question concerns products, please provide details (price, availability, specifications).
    Answer:
    """

    response = bedrock.invoke_model(
        modelId="anthropic.claude-3-haiku-20240307-v1:0",
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7
        })
    )

    body_bytes = response['body'].read()
    response_body = json.loads(body_bytes)
    return response_body['content'][0]['text']

def lambda_handler(event, context):
    """
    Main Lambda function - handles queries from API Gateway

    RAG logic:
    1) question_embedding = embed(question)
    2) docs = vector_db.search(question_embedding)
    3) answer = generate_response_with_claude(question, docs)
    """

    if event.get('requestContext', {}).get('http', {}).get('method') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': ''
        }

    try: 
        body = json.loads(event.get('body', '{}'))
        question = body.get('message', '')

        if not question:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS'
                },
                'body': json.dumps({
                    'error': 'No question in the request'
                })
            }

        question_embedding = embed_text(question)

        docs = search_similar_chunks(question_embedding, top_k=3)

        if not docs:
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application-json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS'
                },
                'body': json.dumps({
                    'response': 'Sorry, I can not find an answer'
                })
            }

        answer = generate_response_with_claude(question, docs)

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': json.dumps({
                'response': answer,
                'sources_count': len(docs)
            })
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': "application/json",
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': json.dumps({
                'error': f"Server error: {str(e)}"
            })
        }