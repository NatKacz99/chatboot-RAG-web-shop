import boto3
import json
import uuid
from chunking import load_and_split

BUCKET_NAME = "rag-shop-vectors"
KNOWLEDGE_BASE = "knowledge_base_for_RAG.txt"

bedrock = boto3.client("bedrock-runtime")
s3 = boto3.client("s3")

def embed_text(text: str) -> list:
    response = bedrock.invoke_model(
        modelId="amazon.titan-embed-text-v2:0",
        body = json.dumps({
            "inputText": text
        })
    )
    return json.loads(response["body"].read())["embedding"]

def store_chunk_in_s3(chunk: str, embedding: list):
    object_key = f"vectors/{uuid.uuid4()}.json"

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=object_key,
        Body=json.dumps({
            "content": chunk,
            "embedding": embedding,
            "metadata": {
                "source": "knowledge_base"
            }
        }),
        ContentType="application/json"
    )

def main():
    chunks = load_and_split(KNOWLEDGE_BASE)

    print(f'Chunks number: {len(chunks)}')

    for i, chunk in enumerate(chunks):
        embedding = embed_text(chunk)
        store_chunk_in_s3(chunk, embedding)
        print(f"Saved chunk {i + 1}/{len(chunks)}")

if __name__ == "__main__":
    main()

