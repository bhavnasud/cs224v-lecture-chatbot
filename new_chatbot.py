import requests
import os
import json
from together import Together

os.environ["TOGETHER_API_KEY"] = ""
together_client = Together(api_key=os.environ["TOGETHER_API_KEY"])

def fetch_from_rag(user_queries):  # Accepts a list of queries now
    rag_endpoint = "https://search.genie.stanford.edu/stanford_MED275"
    rag_payload = {
        "query": user_queries,  # Now expects a list of queries
        "rerank": True,
        "num_blocks_to_rerank": 20,
        "num_blocks": 3
    }
    rag_headers = {
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(rag_endpoint, headers=rag_headers, data=json.dumps(rag_payload))
        response.raise_for_status()  # Checks for HTTP request errors
        rag_data = response.json()
        json_rag_data = json.dumps(rag_data)
        return json_rag_data
        # all_contents = []
        # for entry in rag_data:
        #     for result in entry['results']:
        #         content = result.get('content', '')  # Default to empty string if 'content' is not present
        #         all_contents.append(content)

    except requests.RequestException as e:
        print("HTTP Status Code:", response.status_code)  # Additional debugging information
        print("Response Text:", response.text)
        print("Error contacting RAG system:", e)
        return []

    # return all_contents

def together_generation(prompt):
    try:
        response = together_client.completions.create(
            model="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            prompt=prompt,
            max_tokens=200,  
            temperature=0.5,  
        )
        
        if response.choices and response.choices[0].text.strip():
            return response.choices[0].text.strip()
        else:
            return "I'm sorry, that is outside my knowledge capabilites. Please try again."
            
    except Exception as e:
        print("Error generating response:", e)
        return "There was an issue generating a response. Please try again later."

def generate_response_with_llm(user_query, documents, prev_context):
    # Combine the retrieved documents into a single text block
    # retrieved_text = " ".join(documents)

    # Format the prompt to provide context and the user query
    prompt = (
        f"You are a chatbot answering student questions about MED 275, a lung cancer course taught by Prof. Bryant Lin at Stanford University. Use only the provided context (from current or previous queries) and conversation history to respond. If specific details are unavailable, inform the user with something like, 'That topic wasn’t covered in the information I have so far, but it might appear in later lectures or supplementary materials.' Reuse information from past responses if relevant, but do not create new information beyond what’s provided. If entirely missing, state, 'I'm sorry, I don't have enough information on that topic.\n\n"
        f"Maintain a conversational tone, cite sources naturally in sentences (e.g., 'In Lecture 1, on Diagnosis and Screening, they discussed...'), and do not compile citations at the end.\n\n"
        f"User Question:\n{user_query}\n\n"
        f"Context:\n{documents}\n\n"
        f"Previous Conversation History:\n{prev_context}\n\n"
        f"Answer:"
    )
    # Generate a response using the Together API
    response = together_generation(prompt)
    return response

def chatbot():
    print("Welcome to the Terminal Chatbot! Type 'exit' to quit.")
    prev_context = ""
    while True:
        user_query = input("You: ")
        if user_query.lower() == "exit":
            break

        # Fetch relevant documents using RAG
        documents = fetch_from_rag(user_query)

        # Generate a response with the LLM using RAG documents as context
        response = generate_response_with_llm(user_query, documents, prev_context)

        prev_context += "query: {}, documents: {}, response: {}".format(user_query, documents, response)
        
        # Print the chatbot response
        print(f"Bot: {response}")

if __name__ == "__main__":
    chatbot()
