import requests
import os
import json
from together import Together
from collections import deque
from pydantic import BaseModel, Field
import together

# Define the schema for the output
class RelevantDocumentIndices(BaseModel):
    indices: list[int] = Field(description="The document indices that are relevant to the user query")
class Chatbot:
    def __init__(self, api_key):
        self.together_client = Together(api_key=api_key)
        self.together = Together()
        self.documents_queue = deque([])
        self.prev_context = ""
    def _fetch_from_rag(self, user_queries):  # Accepts a list of queries now
        rag_endpoint = "https://search.genie.stanford.edu/stanford_MED275_v2"
        rag_payload = {
            "query": user_queries,  # Now expects a list of queries
            "rerank": True,
            "num_blocks_to_rerank": 25,
            "num_blocks": 10 # TODO: potentially increase this to 10
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

    def _together_generation(self, prompt):
        try:
            response = self.together_client.completions.create(
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

    def _generate_response_with_llm(self, user_query, documents, prev_context):
        # Format the prompt to provide context and the user query
        prompt = (
            f"You are a chatbot answering student questions about MED 275, a lung cancer course taught by Prof. Bryant Lin at Stanford University."
            f"Use only the provided Context, User Question and Previous Conversation History to respond. If specific details are unavailable,"
            f"inform the user with something like, 'That topic wasn’t covered in the information I have so far, but it might appear in later lectures or"
            f"supplementary materials.' Reuse information from past responses if relevant, but do not create new information beyond what’s provided."
            f"If entirely missing, state, 'I'm sorry, I don't have enough information on that topic.\n\n"
            f"If asked for a recommendation, you can provide relevant URLs.\n\n"
            f"Only answer the student's question.\n\n"
            # f"Maintain a conversational tone, cite sources naturally in sentences (e.g., 'In Lecture 1, on Diagnosis and Screening, they discussed...'), and do not compile citations at the end.\n\n"
            f"Cite the source used to generate each sentence in the response by adding a shortened version of the section_title (Less than 30 characters) of the source in parenthesis after the sentence.\n\n"
            f"If citing a lecture, also include the start and end time of the part of the lecture you are citing.\n\n"
            f"For example, when citing a lecture 2, cite that sentence with (Lecture 2, start_time-end_time min)"
            f"Previous Conversation History:\n{prev_context}\n\n"
            f"User Question:\n{user_query}\n\n"
            f"Context:\n{documents}\n\n"
            f"Answer:"
        )
        # Generate a response using the Together API
        response = self._together_generation(prompt)
        return response

    def _filter_relevant_documents(self, documents, prev_context, user_query):
        # Pre-process documents by removing unwanted keys
        for document in documents:
            document.pop("similarity_score", None)
            document.pop("probability_score", None)

        # Prepare the prompt for the LLM
        messages = [
            {
                "role": "system",
                "content": f"The following is a list of documents that may be relevant to the user query. "
                        f"Analyze the documents and user query carefully. "
                        f"Return only the indices of documents that contain information that answer the user query, using the format {{\"indices\": [<indices>]}}. "
                        f"Ensure indices are within the range 0 to {len(documents) - 1}. If no documents are relevant, return {{\"indices\": []}}. "
                        f"Do not return anything else."
            },
            {
                "role": "user",
                "content": json.dumps({
                    "user_query": user_query,
                    "prev_context": prev_context,
                    "documents": documents
                })
            }
        ]

        # Call the LLM without using a structured response format
        extract = self.together.chat.completions.create(
            messages=messages,
            model="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"
        )

        # Parse the response content
        try:
            print(extract.choices[0].message.content)
            response_content = json.loads(extract.choices[0].message.content)
            print(response_content)
            indices = response_content.get("indices", [])
        except (json.JSONDecodeError, KeyError):
            print("Failed to parse LLM response. Returning an empty list of relevant documents.")
            indices = []

        # Filter relevant documents based on indices
        relevant_documents = []
        for index in indices:
            if 0 <= index < len(documents):
                relevant_documents.append(documents[index])
            else:
                # Debugging invalid indices
                print(f"Invalid index: {index}")
        
        # Debugging output
        print("Query ", user_query)
        print("Number of documents:", len(documents))
        print("Number of relevant documents:", len(relevant_documents))
        print("Relevant documents:", relevant_documents)
        
        return relevant_documents
    
    def _generate_llm_rag_query(self, prev_context, user_query, irrelevant_documents):
        prompt = (
            f"You are a highly intelligent and precise assistant tasked with refining user queries to retrieve the most relevant documents "
            f"from a Retrieval-Augmented Generation (RAG) system for a course called MED 275.\n\n"
            f"In this case, a previous search based on the embedded user query returned no relevant documents.\n\n"
            f"Your goal is to rewrite the query to improve relevance by:\n\n"
            f"1. Removing generic terms or words likely to result in irrelevant matches.\n\n"
            f"2. Adding specific keywords or phrases that are closely associated with the user intent.\n\n"
            f"3. Ensure the new query is concise, unambiguous, and targeted to the user's request.\n\n"
            f"Context from the previous conversation:\n{prev_context}\n\n"
            f"The user's query:\n{user_query}\n\n"
            f"Previously retrieved irrelevant documents:\n{json.dumps(irrelevant_documents)}\n\n"
            f"Provide only the rewritten query as output in a single line, without any additional text, explanations, or formatting.\n\n"
        )
        # Generate a response using the Together API
        response = self._together_generation(prompt)
        return response.strip()
    
    def clear_queue_and_prev_context(self):
        self.documents_queue.clear()
        self.prev_context = ""

    def get_response(self, user_query):
        # Potential fail cases: querying with time range of lecture, asking for recommendations -> should lead to graceful failure or cite additional resources,
        # asking about a lecture that doesn't exist
        if user_query == "":
            return "Please enter a question or type 'exit' to quit."

        # Fetch relevant documents using RAG
        documents = self._fetch_from_rag(user_query)
        self.documents_queue.append(documents)
        if len(self.documents_queue) > 3: # TODO: potentially increase length of queue
            self.documents_queue.popleft()
        
        documents_list = []
        for item in self.documents_queue:
            if len(item) > 0:
                documents_list.extend(item[0]["results"])
        relevant_documents = self._filter_relevant_documents(documents_list, self.prev_context, user_query)
        if len(relevant_documents) == 0:
            print("No relevant documents, generating LLM query!!")
            # TODO: also generate llm rag query if unable to formulate a response based on query
            llm_rag_query = self._generate_llm_rag_query(self.prev_context, user_query, self.documents_queue[-1])
            print("LLM RAG query is ", llm_rag_query)
            documents = self._fetch_from_rag(llm_rag_query)
            self.documents_queue[-1].extend(documents)
            documents_list = []
            for item in self.documents_queue:
                if len(item) > 0:
                    documents_list.extend(item[0]["results"])
            relevant_documents = self._filter_relevant_documents(documents_list, self.prev_context, user_query)
            if len(relevant_documents) == 0:
                print("Still no relevant documents")
                response = "No relevant documents"
            else:
                response = self._generate_response_with_llm(user_query, json.dumps(relevant_documents), self.prev_context)
        else:
            # Generate a response with the LLM using RAG documents as context
            response = self._generate_response_with_llm(user_query, json.dumps(relevant_documents), self.prev_context)
            # if "have enough information" in response or "wasn’t covered in the information" in response:
            #     print(relevant_documents)
        self.prev_context += "query: {}, response: {}".format(user_query, response)
        return f"{response}"
