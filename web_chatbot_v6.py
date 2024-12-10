import requests
import os
import json
from together import Together
from collections import deque
from pydantic import BaseModel, Field
import together
import re
from enum import Enum

class DocumentTitle(str, Enum):
    lectures = "Lectures"
    readings = "Readings"
    slides = "Slides"

class LLMGeneratedQuery(BaseModel):
    updated_query: str = Field(description="Rewritten query that will return more relevant embedding matches")
    document_title: DocumentTitle = Field(None, description="Optional field to filter returned document titles by")

class Chatbot_v6:
    def __init__(self, api_key):
        self.together_client = Together(api_key=api_key)
        self.together = Together()
        self.documents_queue = deque([])
        self.prev_context = ""

    def _fetch_from_rag(self, user_queries, document_title=None):  # Accepts a list of queries now
        rag_endpoint = "https://search.genie.stanford.edu/stanford_MED275_v3"
        rag_payload = {
            "query": user_queries,  
            "rerank": True,
            "num_blocks_to_rerank": 25,
            "num_blocks": 10
        }
        if document_title:
            rag_payload["search_filters"] = [{"field_name": "document_title", "filter_type": "eq", "field_value": document_title}]
        rag_headers = {
            "Content-Type": "application/json"
        }
        try:
            response = requests.post(rag_endpoint, headers=rag_headers, data=json.dumps(rag_payload))
            response.raise_for_status() 
            rag_data = response.json()

        except requests.RequestException as e:
            print("HTTP Status Code:", response.status_code)  
            print("Response Text:", response.text)
            print("Error contacting RAG system:", e)
            return []
        return rag_data
    
    def _together_generation_long(self, prompt):
        try:
            response = self.together_client.completions.create(
                model="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
                prompt=prompt,
                max_tokens=500,  
                temperature=0.5,
                repetition_penalty=1
            )
            
            if response.choices and response.choices[0].text.strip():
                return response.choices[0].text.strip()
            else:
                return "I'm sorry, that is outside my knowledge capabilites. Please try again."
                
        except Exception as e:
            print("Error generating response:", e)
            return "There was an issue generating a response. Please try again later."
        
    def _together_generation_eval(self, prompt):
        try:
            response = self.together_client.completions.create(
                model="meta-llama/Llama-3-70b-chat-hf",
                prompt=prompt,
                max_tokens=400,  
                temperature=0,  
            )
            
            if response.choices and response.choices[0].text.strip():
                return response.choices[0].text.strip()
            else:
                return "There was an issue generating a response. Please try again later."
                
        except Exception as e:
            print("Error generating response:", e)
            return "There was an issue generating a response. Please try again later."
        
    def _together_generation_short(self, prompt):
        try:
            response = self.together_client.completions.create(
                model="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
                prompt=prompt,
                max_tokens=100,  
                temperature=0.5,  
            )
            
            if response.choices and response.choices[0].text.strip():
                return response.choices[0].text.strip()
            else:
                return "I'm sorry, that is outside my knowledge capabilites. Please try again."
                
        except Exception as e:
            print("Error generating response:", e)
            return "There was an issue generating a response. Please try again later."

    def add_citations(self, documents):
        updated_documents = []
        for document in documents:
            citation = ""
            print(document["section_title"])
            if document["document_title"] == "Readings":
                parts = document["section_title"].split(">")
                title = parts[0].strip()
                author_pattern = r"\b[A-Za-z]+(?:[A-Z][a-z]*)* et al"
                # Search for the pattern in the section title
                match = re.search(author_pattern, title)
                authors = match.group(0) if match else None
                year = document["last_edit_date"][:4]
                if authors is not None:
                    citation = f"{authors},{year}"
                elif title is not None:
                    citation = f"{title},{year}"
                else:
                    citation = document["section_title"]
            elif document["document_title"] == "Lectures":
                parts = document["section_title"].split(">")
                title = None
                if len(parts) > 1:
                    title = parts[1].strip()
                time_range = document["block_metadata"]["time_range_minutes"]
                if title is None:
                    title = document["section_title"]
                citation = f"{title}, {time_range} minutes"
            elif document["document_title"] == "Slides":
                citation = f"Slides: {document['section_title']}"
            document["citation"] = citation
            updated_documents.append(document)
        return updated_documents

    def _generate_response_with_llm(self, user_query, documents, prev_context):
        # Format the prompt to provide context and the user query
        documents_context = json.dumps(documents, indent=4, separators=",\n")
        prompt = (
            f"You are a chatbot answering medical student questions about MED 275, a lung cancer course taught by Prof. Bryant Lin at Stanford University.\n\n"
            f"Your answers should be detailed and should use the provided Context and Previous Conversation History to answer the User Question.\n\n"
            f"If the context contains no implicitly or explicitly relevant information to the user query, respond only with 'I'm sorry, I don't have enough information on that topic.'\n"
            f"If the context only contains some of the necessary information to answer the query, infer the best possible answer based on the provided information.\n"
            f"Try to use multiple diverse sources if possible.\n"
            f"Do not create new information outside the scope of the provided context, but feel free to synthesize insights if relevant.\n\n"
            f"Where applicable, suggest additional resources, such as course material, relevant URLs, or further steps the user might take.\n\n"
            f"Lectures are 60 minutes long, use the start and end times of lecture in the context to answer questions about time.\n\n"
            f"Cite the source used to generate each sentence in the response by adding the citation field from the relevant document metadata in parenthesis after the sentence.\n\n"
            f"Do not use the word 'context' or 'citation' in your answer.\n\n"
            f"Vary your answer from previous responses, and avoid repeating information in Previous Conversation History.\n\n"
            f"Previous Conversation History:\n{prev_context}\n\n"
            f"User Question:\n{user_query}\n\n"
            f"Context:\n{documents_context}\n\n"
            f"Answer:"
        )
        response = self._together_generation_long(prompt)
        return response

    def _generate_llm_rag_query(self, prev_context, user_query):
        extract = self.together.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"You are a highly intelligent assistant tasked with refining user queries to retrieve the most relevant documents "
                        f"from an embedding search system.\n\n"
                        f"Your goal is to rewrite the user query to improve relevance by:\n\n"
                        f"1. Removing generic terms or words likely to result in irrelevant matches.\n\n"
                        f"2. Adding specific keywords or phrases that are closely associated with the user intent.\n\n"
                        f"3. Ensure the new search query is concise. It is fine if the new query is just one word long.\n\n"
                        f"You also should fill in the document_title field with either 'Lectures', 'Readings', or 'Slides' depending on the user query, or leave it empty if you don't want to filter by any of these kinds of documents.\n\n"
                },
                {
                    "role": "user",
                    "content": json.dumps({
                        "context_from_prev_conversation": prev_context,
                        "user_query": user_query,
                    })
                },
            ],
            model="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            response_format={
                "type": "json_object",
                "schema": LLMGeneratedQuery.model_json_schema(),
            },
        )

        print("LLM generated query ", extract.choices[0].message.content)
        try:
            llm_generated_query = json.loads(extract.choices[0].message.content)
        except Exception as e:
            print("Failed parsing LLM generated RAG query ", str(e))
            print("LLM response ", extract.choices[0].message.content)
            return {}
        return llm_generated_query
    
    def clear_queue_and_prev_context(self):
        self.documents_queue.clear()
        self.prev_context = ""

    def get_response(self, user_query):
        if user_query == "":
            return "Please enter a question"

        # Fetch relevant documents using RAG
        documents = self._fetch_from_rag(user_query)[0]["results"]
        self.documents_queue.append(documents)
        if len(self.documents_queue) > 3: 
            self.documents_queue.popleft()
        
        documents_list = []
        for item in self.documents_queue:
            if len(item) > 0:
                for document in item:
                    document.pop("similarity_score", None)
                    document.pop("probability_score", None)
                documents_list.extend(item)

        documents_list = self.add_citations(documents_list)
        response = self._generate_response_with_llm(user_query, json.dumps(documents_list, indent=4, separators=(",\n")), self.prev_context)
        if "don't have enough information" in response:
            llm_rag_query = self._generate_llm_rag_query(self.prev_context, user_query)
            if llm_rag_query == {} or not llm_rag_query.get("updated_query"):
                return response
            print(f"Not enough information to generate response, generated LLM RAG query: {llm_rag_query}")
            additional_documents = self._fetch_from_rag(llm_rag_query["updated_query"], document_title=llm_rag_query.get("document_title"))[0]["results"]
            for document in additional_documents:
                document.pop("similarity_score", None)
                document.pop("probability_score", None)
            # replace stored documents for this query
            self.documents_queue[-1] = additional_documents
            print("LLM RAG retrieved documents: ", [document['section_title'] for document in additional_documents])
            additional_documents = self.add_citations(additional_documents)
            response = self._generate_response_with_llm(user_query, json.dumps(additional_documents, indent=4, separators=(",\n")), self.prev_context)
        self.prev_context += "\nQuery: {}, Response: {}".format(user_query, response)
        return response
