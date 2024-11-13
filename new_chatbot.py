import requests
import os
import json
from together import Together
from collections import deque
from pydantic import BaseModel, Field
import together

os.environ["TOGETHER_API_KEY"] = "61c3d30d6e3b2cc30504a65a11ddd0acb4d6e8912f32040d831c03285c51caa7"
together_client = Together(api_key=os.environ["TOGETHER_API_KEY"])
together = Together()

def fetch_from_rag(user_queries):  # Accepts a list of queries now
    rag_endpoint = "https://search.genie.stanford.edu/stanford_MED275"
    rag_payload = {
        "query": user_queries,  # Now expects a list of queries
        "rerank": True,
        "num_blocks_to_rerank": 25,
        "num_blocks": 4 # TODO: potentially increase this to 10
    }
    rag_headers = {
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(rag_endpoint, headers=rag_headers, data=json.dumps(rag_payload))
        response.raise_for_status()  # Checks for HTTP request errors
        rag_data = response.json()
        return rag_data

    except requests.RequestException as e:
        print("HTTP Status Code:", response.status_code)  # Additional debugging information
        print("Response Text:", response.text)
        print("Error contacting RAG system:", e)
        return []

def together_generation(prompt):
    try:
        response = together_client.completions.create(
            model="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            prompt=prompt,
            max_tokens=400,  
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
    # Format the prompt to provide context and the user query
    prompt = (
        f"You are a chatbot answering student questions about MED 275, a lung cancer course taught by Prof. Bryant Lin at Stanford University."
        f"Use only the provided context (from current or previous queries) and conversation history to respond. If specific details are unavailable,"
        f"inform the user with something like, 'That topic wasn’t covered in the information I have so far, but it might appear in later lectures or"
        f"supplementary materials.' Reuse information from past responses if relevant, but do not create new information beyond what’s provided."
        f"If entirely missing, state, 'I'm sorry, I don't have enough information on that topic.\n\n"
        f"If asked for a reccomendation, you can provide relevant URLs.\n\n"
        f"Only answer the student's question.\n\n"
        # f"Maintain a conversational tone, cite sources naturally in sentences (e.g., 'In Lecture 1, on Diagnosis and Screening, they discussed...'), and do not compile citations at the end.\n\n"
        f"Cite the source used to generate each sentence in the response by adding the section_title of the source in parenthesis after the sentence.\n\n"
        f"Previous Conversation History:\n{prev_context}\n\n"
        f"User Question:\n{user_query}\n\n"
        f"Context:\n{documents}\n\n"
        f"Answer:"
    )
    # Generate a response using the Together API
    response = together_generation(prompt)
    return response

# Define the schema for the output
class RelevantDocumentIndices(BaseModel):
    indices: list[int] = Field(description="The document indices that are relevant to the user query")

def filter_relevant_documents(documents, prev_context, user_query):
    for doc in documents:
        print(doc)
        print("/n")
    # Call the LLM with the JSON schema
    extract = together.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": f"The following is a list of documents that may be relevant to the user query."
                f"Return the indices of the documents that are relevant to the user query,"
                f"using prev_context as the context of the conversation. Indices must be between 0 and {len(documents) - 1}."
                f"If no documents are relevant, return an empty list."
                f"Only answer in JSON.",
            },
            {
                "role": "user",
                "content": json.dumps({
                    "user_query": user_query,
                    "prev_context": prev_context,
                    "documents": documents
                })
            },
        ],
        model="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        response_format={
            "type": "json_object",
            "schema": RelevantDocumentIndices.model_json_schema(),
        },
    )

    relevant_document_indices = json.loads(extract.choices[0].message.content)
    relevant_documents = []
    print("returned indices ", relevant_document_indices["indices"])
    print("number of documents ", len(documents))
    for index in relevant_document_indices["indices"]:
        if index >= 0 and index < len(documents):
            relevant_documents.append(documents[index])
        # TODO: Remove print statement later. Only for debugging.
        else:
            print(f"Invalid index: {index}")
    return relevant_documents

def chatbot():
    # Potential fail cases: querying with time range of lecture, asking for recommendations -> should lead to graceful failure or cite additional resources,
    # asking about a lecture that doesn't exist
    print("Welcome to the MED 275 Chatbot! Please enter a question. Type 'exit' to quit.")
    prev_context = ""
    documents_queue = deque([])
    while True:
        user_query = input("You: ")
        if user_query.lower() == "exit":
            break
        if user_query == "":
            print(f"Bot: Please enter a question or type 'exit' to quit.")
            continue

        # Fetch relevant documents using RAG
        documents = fetch_from_rag(user_query)
        documents_queue.append(documents)
        if len(documents_queue) > 3: # TODO: potentially increase length of queue
            documents_queue.popleft()
        
        documents_list = []
        for item in documents_queue:
            if len(item) > 0:
                documents_list.extend(item[0]["results"])
        relevant_documents = filter_relevant_documents(documents_list, prev_context, user_query)
        print("Number of relevant documents ", len(relevant_documents))
        if len(relevant_documents) == 0:
            response = "No relevant documents"
            # TODO: have LLM generate RAG query to retrieve potentially relevant documents
        else:
            # Generate a response with the LLM using RAG documents as context
            response = generate_response_with_llm(user_query, json.dumps(relevant_documents), prev_context)

        # TODO: perhaps only include the documents that were used in response
        prev_context += "query: {}, response: {}".format(user_query, response)
        
        # Print the chatbot response
        print(f"Bot: {response}")

if __name__ == "__main__":
    chatbot()
