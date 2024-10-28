# Required Imports
import os
from together import Together
from pinecone import Pinecone
from pinecone import ServerlessSpec
import time
import json

# Set your Together API key and Pinecone API key as environment variables for security (or insert directly for testing)
os.environ["TOGETHER_API_KEY"] = "61c3d30d6e3b2cc30504a65a11ddd0acb4d6e8912f32040d831c03285c51caa7"
os.environ["PINECONE_API_KEY"] = "62011fee-32f3-46e5-85a7-d3c12ba81e84"

# Initialize Together AI Client
together_client = Together(api_key=os.environ["TOGETHER_API_KEY"])
# Load the JSON file
with open("cs224v-lecture-chatbot/chunked_audio_transcriptions_even/MED-275_09-25-2024-0_transcription_output.json", "r") as file:
    data = json.load(file)

# chunk_texts = [entry["text"] for entry in data if "text" in entry]
chunk_texts = ["soup is bad", "pasta is good", "cats are not good", "dogs are great"]

# Step 1: Generate M2-BERT Embeddings for Document Chunks
def generate_m2_bert_embeddings(texts):
    embeddings = []
    for text in texts:
        response = together_client.embeddings.create(input=[text], model="togethercomputer/m2-bert-80M-8k-retrieval")
        embeddings.append(response.data[0].embedding)
    return embeddings

chunk_embeddings = generate_m2_bert_embeddings(chunk_texts)

# Step 2: Initialize Pinecone and Store Embeddings
pinecone_client = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))

# Define the index name and dimensions
index_name = "rag-chatbot-m2bert"
dimension = 768

# Check if the index exists; if not, create it with the appropriate specifications
print("index names:", pinecone_client.list_indexes().names())
if index_name not in pinecone_client.list_indexes().names():
    pinecone_client.create_index(
        name=index_name,
        dimension=dimension,
        metric='cosine',
        spec=ServerlessSpec(
            cloud='aws',    # Change to your cloud provider if needed
            region='us-east-1'  # Update to a valid region
        )
    )
while not pinecone_client.describe_index(index_name).status['ready']:
    time.sleep(1) 

# Access the index
index = pinecone_client.Index(index_name)
time.sleep(1)
print("Index:", index)

# Upsert embeddings with print statements for debugging
for i, embedding in enumerate(chunk_embeddings):
    vector_data = {
        "id": f"chunk-{i}",
        "values": embedding,
        "metadata": {"text": chunk_texts[i]}  # Ensure metadata is included here
    }
    print(f"Upserting vector {i}:")
    print("ID:", vector_data["id"])
    print("Values (first 5 dimensions):", vector_data["values"][:5])  # Print only the first few dimensions
    print("Metadata:", vector_data["metadata"])
    
    # Perform the upsert
    response = index.upsert([vector_data])
    print("Upsert response:", response)

# Check if vectors are now in the index
index_stats = index.describe_index_stats()
print("Index Stats after upsert:", index_stats)


# Step 4: Set up Together AI for Generation
def together_generation(prompt):
    response = together_client.completions.create(
        model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        prompt=prompt,
        max_tokens=150,
        temperature=0.7,
    )
    return response.choices[0].text

def rag_chatbot(query):
    # Generate the embedding for the user query
    response = together_client.embeddings.create(input=[query], model="togethercomputer/m2-bert-80M-8k-retrieval")
    query_vector = response.data[0].embedding

    print(index.describe_index_stats())

    # Retrieve relevant chunks based on query using Pinecone's similarity search
    search_results = index.query(vector=query_vector, top_k=5, include_metadata=True)

    # Print the search results
    print("Search Results:", search_results)

    # Check if any matches were returned and retrieve text from metadata
    if search_results is not None and "matches" in search_results and search_results["matches"]:
        retrieved_text = " ".join([match["metadata"]["text"] for match in search_results["matches"] if "metadata" in match and "text" in match["metadata"]])
    else:
        retrieved_text = "No relevant information found."

    # Print the retrieved text
    print("Retrieved Text:", retrieved_text)

    # Create prompt with context and query
    prompt = f"Based on the following context answer the question: {query}\n\n Context: {retrieved_text}."
    response = together_generation(prompt)
    return response

# Test the RAG Chatbot
user_query = "Are cats good?"
response = rag_chatbot(user_query)
print("Chatbot Response:", response)

# Optional: Clean up Pinecone index after use
pinecone_client.delete_index(index_name)