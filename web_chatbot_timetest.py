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
    time_range_minutes: tuple[int, int] = Field(None, description="Optional field to filter returned document time ranges by [startime, endtime] in minutes")

class Chatbot_v7:
    def __init__(self, api_key):
        self.together_client = Together(api_key=api_key)
        self.together = Together()
        self.documents_queue = deque([])
        self.prev_context = ""

    def _fetch_from_rag(self, user_queries, document_title=None, time_range_minutes=[-1,-1]):  # Accepts a list of queries now
        rag_endpoint = "https://search.genie.stanford.edu/stanford_MED275_v3"
        rag_payload = {
            "query": user_queries,  # Now expects a list of queries
            "rerank": True,
            "num_blocks_to_rerank": 20,
            "num_blocks": 10
        }
        if document_title:
            rag_payload["search_filters"] = [{"field_name": "document_title", "filter_type": "eq", "field_value": document_title}]
        rag_headers = {
            "Content-Type": "application/json"
        }
        try:
            response = requests.post(rag_endpoint, headers=rag_headers, data=json.dumps(rag_payload))
            response.raise_for_status()  # Checks for HTTP request errors
            rag_data = response.json()

        except requests.RequestException as e:
            print("HTTP Status Code:", response.status_code)  # Additional debugging information
            print("Response Text:", response.text)
            print("Error contacting RAG system:", e)
            return []
        if document_title != "Slides" and document_title != "Readings" and time_range_minutes != [-1,-1]:
            results_to_keep = [] 
            for result in rag_data[0]['results']:
                time_range = re.match(r"^(\d+)-(\d+)$", result['block_metadata']['time_range_minutes'])
                if time_range:
                    start = int(time_range.group(1)) - 5
                    print("start", start)
                    end = int(time_range.group(2)) + 5
                    print("end", end)
                    if start <= time_range_minutes[1] and end >= time_range_minutes[0]:
                        print("bot_start", time_range_minutes[0])
                        print("bot_end", time_range_minutes[1])
                        results_to_keep.append(result)
            rag_data[0]['results'] = [result for result in rag_data[0]['results'] if result in results_to_keep]
        print("time", time_range_minutes)
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
        # documents_context = "[\"document_title\"\n\"Readings\",\n        \"section_title\"\n\"How Timely Is Diagnosis of Lung Cancer? Cohort Study of Individuals with Lung Cancer Presenting in Ambulatory Care in the United States (Suchsland et al) > Results > Selection of Cohort\",\n        \"content\"\n\"A total of 7883 patients with lung cancer were identified over the study period (Figure 1), of whom 225 were excluded as they had tracheal cancer (not shown in Figure 1). Separately, SEER registry matched 5540 of the 7883 UWM patients with lung cancer, of whom 1340 did not have a first primary tumor located in lungs and/or the histology code did not meet inclusion criteria and were excluded. Following linkage of the patients identified from the UW EDW (n = 7658) and those from SEER (n = 4200), a set of 4115 patients were identified common to both. We excluded patients who did not meet the ambulatory care definition (n = 3108), and those who had not received chest CT imaging at UWM (n = 243). Additional patients were excluded after review of missing or discrepant pathology data (n = 33) and those who lacked any ICD codes that could be used to calculate comorbidity (n = 20). The final cohort consisted of 711 patients.\\nfrom the UW EDW (n = 7658) and those from SEER (n = 4200), a set of 4115 patients were identified common to both. We excluded patients who did not meet the ambulatory care definition (n = 3108), and those who had not received chest CT imaging at UWM (n = 243). Additional patients were excluded after review of missing or discrepant pathology data (n = 33) and those who lacked any ICD codes that could be used to calculate comorbidity (n = 20). The final cohort consisted of 711 patients.\",\n        \"last_edit_date\"\n\"2022-11-23T00:00:00\",\n        \"url\"\n\"https://pmc.ncbi.nlm.nih.gov/articles/PMC9740627\",\n        \"num_tokens\"\n0,\n        \"block_metadata\"\n{\n            \"citation\"\n\"Readings, How Timely Is Diagnosis of Lung Cancer?\"}\n    }\n, {\n        \"document_title\"\n\"Slides\",\n        \"section_title\"\n\"MED 275 - Epidemiology and Cultural Considerations\",\n        \"content\"\n\"2024 American Cancer Society \\u2013  Lung Cancer 5-year Survival: 2013  to 2019\\n25% for all stages\\nAsian: favorable prognostic  factor independent of  smoking status\\nwww.cancer.org\\nJTO 2009\\nMortality remains high, due to late diagnosis\\nStage\\n5-year relative survival (%)\\n% of lung CA\\nLocalized\\n24%\\n61.2\\n33.5\\nRegional\\n22%\\n7.0\\nDistant\\n46%\\nACS SEER 2012-2018\\nAnnual screening for lung cancer  recommended for high-risk adults\\nFirst ever USPSTF recommendation\\n(age 55-80, 30+ pack-years, smoked in last 15 yrs)\\n2013\\nUpdated USPSTF recommendation\\n(age 50-80, 20+ pack-years, smoked in last 15 yrs)\\n2021\\n2011\\n2020\\nNational Lung Screening  Trial results published\\nNELSON Trial results  published\\nWhat is Lung cancer  screening (LCS)?\\n1 min Low-Dose CT scan:  NOT an XRAY\\nAnnual CT scan\\n2021 USPSTF guidelines:\\nAge 50 \\u2013 80, currently  smoke or 20 pack year  history, quit within past  15 years\\nAs LCS volume increases, more  early-stage lung cancer picked up\\nAs LCS volume increased:\\n0% Lung Cancer Dx in\\n2014\\n20% Lung Cancer Dx in\\n2019\\nStage-specific incidence rates\\nincreased for stage I cancer  (AAPC = 8.0 [95% CI: 0.8\\u201315.7])\\nand declined for stage IV  disease (AAPC = \\u22126.0 [95%\\nCI: \\u221211.2 to \\u22120.5])\\nAsian Americans continue to be  diagnosed more with Stage IV\\nDespite  increase in  LCS, Asian  Americans  continued to  be dx with  more Stage IV  than Stage I vs.  Caucasians\\nStage IV  predominant\\nPotter AL,BMJ. 2022 Mar\\nAsian American Disparities and  Cancer\\nFastest-growing US racial group \\u2013 24 million\\nCancer - leading cause of death in both men and  women, not heart disease!!\\nHistorical prejudices, racism, cultural/language\\nbarriers, \\u201cModel minority myth\\u201d\\nOnly 0.17% of the total NIH budget funds Asian  American Research\\n2% of clinical trial participants\\n\\u201cOur problems never make the  headlines.\\u201d\\t- Susan Shinagawa\\nJNCI 2022\\nCDC/NCHS 2021\\nAsians are the most rapidly growing racial/ethnic group in the US\\nFrom U.S. Census\",\n        \"last_edit_date\"\n\"2024-10-30T00:00:00\",\n        \"url\"\n\"https://canvas.stanford.edu/courses/198463/files?preview=14191559\",\n        \"num_tokens\"\n0,\n        \"block_metadata\"\n{\n            \"author\"\n\"Jeffrey Velotta (MD, FACS)\",\n            \"slide_range\"\n\"Slide 10-17\"\n        \"citation\"\n\"Slides 10-17, Lecture 5\"\n }\n    }, {\n        \"document_title\"\n\"Lectures\",\n        \"section_title\"\n\"Lecture 5\",\n        \"content\"\n\"I have no family history. I never smoked, and the lung lesion was picked up on a chest X-ray that I did for positive PPD. The final pathology revealed that the cancer has spread to the methastinum, giving me a stage IIIA diagnosis. I underwent lobectomy, radiation, chemotherapy, as well as oxymetinib, a targeted therapy for 3 years, which I finished in, uh, end of 2023. Uh, in May of this year, uh, I underwent surveillance, and the cancer has recurred and has spread to the spine and also the left adrenal gland. Uh, I was put back on a regimen consisting of targeted therapy as well as chemotherapeutic agents. Uh, I want to share this story with you, uh, to increase awareness. I was shocked by the experience. I was shocked a lot because I developed cancer. I was shocked because I am I I never smoke. I'm totally asymptomatic, and I don't have any family history, and I'm diagnosed to have lung cancer. Thank you for your attention. My lung cancer was detected instantly during a workup for fishbone. What happened was 3 months ago. I had persistent right neck pain for 10 days. I remember that I swallowed fishbone about 10 days ago. Since I'm radiologist, I went to get neck x-ray to look for fishbone.\",\n        \"last_edit_date\"\n\"2024-10-30T00:00:00\",\n        \"url\"\n\"https://mediasite.stanford.edu/Mediasite/Play/f6963fafb2f54cebb88957090a4785951d\",\n        \"num_tokens\"\n0,\n        \"block_metadata\"\n{\n            \"time_range_minutes\"\n\"32-37\",\n            \"speakers\"\n\"Jeffrey Velotta (MD, FACS), Bryant Lin (MD)\",\n            \"lecture_title\"\n\"Epidimeology and Cultural Considerations\"\n        \"citation\"\n\"Lecture 5, Epidimeology and Cultural Considerations\"}\n    }]"
        prompt = (
            f"You are a chatbot answering medical student questions about MED 275, a lung cancer course taught by Prof. Bryant Lin at Stanford University.\n\n"
            f"Your answers should be long, detailed and should use the provided Context and Previous Conversation History to answer the User Question.\n\n"
            f"Answer in a confident, informative tone.\n\n"
            f"If the context contains no implicitly or explicitly relevant information to the user query, respond only with 'I'm sorry, I don't have enough information on that topic.'\n"
            f"If the context only contains some of the necessary information to answer the query, infer the best possible answer based on the provided information.\n"
            f"Try to use multiple sources if possible.\n"
            f"Do not create new information outside the scope of the provided context, but feel free to synthesize insights if relevant.\n\n"
            f"Where applicable, suggest additional resources, such as course material, relevant URLs, or further steps the user might take.\n\n"
            f"Lectures are 60 minutes long, use the start and end times of lecture in the context to answer questions about time.\n\n"
            f"Cite the source used to generate each sentence in the response in parenthesis after the sentence. Use the 'citation' field in the context to cite the source.\n\n"
            f"Vary your answer from previous responses, and avoid repeating information in Previous Conversation History.\n\n"
            f"Previous Conversation History:\n{prev_context}\n\n"
            f"User Question:\n{user_query}\n\n"
            f"Context:\n{documents_context}\n\n"
            f"Answer:"
        )
        # Generate a response using the Together API
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
                        f"You also can fill in the document_title field with either 'Lectures', 'Readings', or 'Slides' depending on the user query. If the user does not mention Lectures, Readings, or Slides or leave it empty..\n\n"
                        f"You also can fill in the time_range_minutes field with the relevant start time and end time in minutes depending on the user query. A lecture is 60 minutes long. The beginning is between 0 and 15 minutes, the end is between 45 and 60 minutes. You should set it to [-1,-1] if the user does not mention time or asks for a summary.\n\n"
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
        llm_rag_query = self._generate_llm_rag_query(self.prev_context, user_query)
        if llm_rag_query["time_range_minutes"] != [-1,-1]:
            documents = self._fetch_from_rag(llm_rag_query["updated_query"], document_title=llm_rag_query.get("document_title"), time_range_minutes=llm_rag_query.get("time_range_minutes"))[0]["results"]
        else:
            documents = self._fetch_from_rag(llm_rag_query["updated_query"], document_title=llm_rag_query.get("document_title"), time_range_minutes=llm_rag_query.get("time_range_minutes"))[0]["results"]
            documents += self._fetch_from_rag([user_query, llm_rag_query["updated_query"]])[0]["results"]

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
        print("hi")
        print("documents_list", documents_list)
        response = self._generate_response_with_llm(user_query + "or" + llm_rag_query["updated_query"], json.dumps(documents_list, indent=4, separators=(",\n")), self.prev_context)
        # if "don't have enough information" in response:
        #     llm_rag_query = self._generate_llm_rag_query(self.prev_context, user_query)
        #     if llm_rag_query == {} or not llm_rag_query.get("updated_query"):
        #         return response
        #     print(f"Not enough information to generate response, generated LLM RAG query: {llm_rag_query}")

        #     additional_documents = self._fetch_from_rag(llm_rag_query["updated_query"], document_title=llm_rag_query.get("document_title"), time_range_minutes=llm_rag_query.get("time_range_minutes"))[0]["results"]
        #     for document in additional_documents:
        #         document.pop("similarity_score", None)
        #         document.pop("probability_score", None)
        #     # replace stored documents for this query
        #     if len(self.documents_queue) > 0:
        #         self.documents_queue[-1] = additional_documents
        #     else:
        #         self.documents_queue.append(additional_documents)
        #     print("LLM RAG retrieved documents: ", [document['section_title'] for document in additional_documents])
        #     additional_documents = self.add_citations(additional_documents)
        #     response = self._generate_response_with_llm(user_query, json.dumps(additional_documents, indent=4, separators=(",\n")), self.prev_context)
        self.prev_context += "\nQuery: {}, Response: {}".format(user_query, response)
        return response
    
# os.environ["TOGETHER_API_KEY"] = "30cde163d78fa4c02d653ab94957386b6dcfb1c370e2a04c8678dc17197794e1"

# # Initialize your chatbot with the API key
# chatbot = Chatbot_v6(api_key=os.environ["TOGETHER_API_KEY"])

# print("response", chatbot._fetch_from_rag(["What is discussed at the end of lecture 1?"], document_title="Lectures", time_range_minutes=(30, 60)))
