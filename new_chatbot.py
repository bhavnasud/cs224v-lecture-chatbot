import requests
import os
import json
from together import Together

os.environ["TOGETHER_API_KEY"] = 
together_client = Together(api_key=os.environ["TOGETHER_API_KEY"])

def fetch_from_rag(user_query):
    # Replace `rag_endpoint` with the RAG system’s API URL
    # rag_endpoint = "https://api.ragsystem.com/retrieve"
    # rag_payload = {"query": user_query}
    # rag_headers = {"Content-Type": "application/json"}
    return ["Calgary is a city", "Alberta is a province", "Canada is a country"]

    # try:
    #     response = requests.post(rag_endpoint, headers=rag_headers, data=json.dumps(rag_payload))
    #     response.raise_for_status()
    #     rag_data = response.json()  # Assuming RAG returns relevant documents/snippets in JSON format
    #     return rag_data.get("documents", [])  # Retrieve documents from the response
    # except requests.RequestException as e:
    #     print("Error contacting RAG system:", e)
    #     return []

def together_generation(prompt):
    try:
        response = together_client.completions.create(
            model="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            prompt=prompt,
            max_tokens=200,  # Increased max_tokens for testing
            temperature=0.5,  # Reduced temperature for more deterministic output
        )
        
        if response.choices and response.choices[0].text.strip():
            return response.choices[0].text.strip()
        else:
            return "I'm sorry, that is outside my knowledge capabilites. Please try again."
            
    except Exception as e:
        print("Error generating response:", e)
        return "There was an issue generating a response. Please try again later."

def generate_response_with_llm(user_query, documents):
    # Combine the retrieved documents into a single text block
    retrieved_text = " ".join(documents)

    # Format the prompt to provide context and the user query
    prompt = (
        f"Please use the provided context to answer the user's question. If the context is insufficient "
        f"or does not directly answer the question, respond with 'I don't know'.\n\n"
        f"User Question: {user_query}\n\n"
        f"Context:\n{retrieved_text}\n\n"
        f"Answer:"
    )
    # Generate a response using the Together API
    response = together_generation(prompt)
    return response

def chatbot():
    print("Welcome to the Terminal Chatbot! Type 'exit' to quit.")
    while True:
        user_query = input("You: ")
        if user_query.lower() == "exit":
            break

        # Fetch relevant documents using RAG
        documents = fetch_from_rag(user_query)

        # Generate a response with the LLM using RAG documents as context
        response = generate_response_with_llm(user_query, documents)
        
        # Print the chatbot response
        print(f"Bot: {response}")

if __name__ == "__main__":
    chatbot()
