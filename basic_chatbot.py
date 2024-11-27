import requests
import json
from together import Together
from collections import deque

class BasicChatbot:
    def __init__(self, api_key):
        self.together_client = Together(api_key=api_key)
        self.together = Together()
        self.documents_queue = deque([])
        self.prev_context = ""

    def _fetch_from_rag(self, user_queries):  # Accepts a list of queries now
        rag_endpoint = "https://search.genie.stanford.edu/stanford_MED275_v3"
        rag_payload = {
            "query": user_queries,  # Now expects a list of queries
            "rerank": True,
            "num_blocks_to_rerank": 30,
            "num_blocks": 15
        }
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
        return rag_data

    def _together_generation_long(self, prompt):
        try:
            response = self.together_client.completions.create(
                model="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
                prompt=prompt,
                max_tokens=500,  
                temperature=1,  
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
                model="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
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

    def _generate_response_with_llm(self, user_query, documents, prev_context):
        # Format the prompt to provide context and the user query
        documents_context = json.dumps(documents, indent=4, separators=",\n")
        # documents_context = "[\"document_title\"\n\"Readings\",\n        \"section_title\"\n\"How Timely Is Diagnosis of Lung Cancer? Cohort Study of Individuals with Lung Cancer Presenting in Ambulatory Care in the United States (Suchsland et al) > Results > Selection of Cohort\",\n        \"content\"\n\"A total of 7883 patients with lung cancer were identified over the study period (Figure 1), of whom 225 were excluded as they had tracheal cancer (not shown in Figure 1). Separately, SEER registry matched 5540 of the 7883 UWM patients with lung cancer, of whom 1340 did not have a first primary tumor located in lungs and/or the histology code did not meet inclusion criteria and were excluded. Following linkage of the patients identified from the UW EDW (n = 7658) and those from SEER (n = 4200), a set of 4115 patients were identified common to both. We excluded patients who did not meet the ambulatory care definition (n = 3108), and those who had not received chest CT imaging at UWM (n = 243). Additional patients were excluded after review of missing or discrepant pathology data (n = 33) and those who lacked any ICD codes that could be used to calculate comorbidity (n = 20). The final cohort consisted of 711 patients.\\nfrom the UW EDW (n = 7658) and those from SEER (n = 4200), a set of 4115 patients were identified common to both. We excluded patients who did not meet the ambulatory care definition (n = 3108), and those who had not received chest CT imaging at UWM (n = 243). Additional patients were excluded after review of missing or discrepant pathology data (n = 33) and those who lacked any ICD codes that could be used to calculate comorbidity (n = 20). The final cohort consisted of 711 patients.\",\n        \"last_edit_date\"\n\"2022-11-23T00:00:00\",\n        \"url\"\n\"https://pmc.ncbi.nlm.nih.gov/articles/PMC9740627\",\n        \"num_tokens\"\n0,\n        \"block_metadata\"\n{\n            \"citation\"\n\"Readings, How Timely Is Diagnosis of Lung Cancer?\"}\n    }\n, {\n        \"document_title\"\n\"Slides\",\n        \"section_title\"\n\"MED 275 - Epidemiology and Cultural Considerations\",\n        \"content\"\n\"2024 American Cancer Society \\u2013  Lung Cancer 5-year Survival: 2013  to 2019\\n25% for all stages\\nAsian: favorable prognostic  factor independent of  smoking status\\nwww.cancer.org\\nJTO 2009\\nMortality remains high, due to late diagnosis\\nStage\\n5-year relative survival (%)\\n% of lung CA\\nLocalized\\n24%\\n61.2\\n33.5\\nRegional\\n22%\\n7.0\\nDistant\\n46%\\nACS SEER 2012-2018\\nAnnual screening for lung cancer  recommended for high-risk adults\\nFirst ever USPSTF recommendation\\n(age 55-80, 30+ pack-years, smoked in last 15 yrs)\\n2013\\nUpdated USPSTF recommendation\\n(age 50-80, 20+ pack-years, smoked in last 15 yrs)\\n2021\\n2011\\n2020\\nNational Lung Screening  Trial results published\\nNELSON Trial results  published\\nWhat is Lung cancer  screening (LCS)?\\n1 min Low-Dose CT scan:  NOT an XRAY\\nAnnual CT scan\\n2021 USPSTF guidelines:\\nAge 50 \\u2013 80, currently  smoke or 20 pack year  history, quit within past  15 years\\nAs LCS volume increases, more  early-stage lung cancer picked up\\nAs LCS volume increased:\\n0% Lung Cancer Dx in\\n2014\\n20% Lung Cancer Dx in\\n2019\\nStage-specific incidence rates\\nincreased for stage I cancer  (AAPC = 8.0 [95% CI: 0.8\\u201315.7])\\nand declined for stage IV  disease (AAPC = \\u22126.0 [95%\\nCI: \\u221211.2 to \\u22120.5])\\nAsian Americans continue to be  diagnosed more with Stage IV\\nDespite  increase in  LCS, Asian  Americans  continued to  be dx with  more Stage IV  than Stage I vs.  Caucasians\\nStage IV  predominant\\nPotter AL,BMJ. 2022 Mar\\nAsian American Disparities and  Cancer\\nFastest-growing US racial group \\u2013 24 million\\nCancer - leading cause of death in both men and  women, not heart disease!!\\nHistorical prejudices, racism, cultural/language\\nbarriers, \\u201cModel minority myth\\u201d\\nOnly 0.17% of the total NIH budget funds Asian  American Research\\n2% of clinical trial participants\\n\\u201cOur problems never make the  headlines.\\u201d\\t- Susan Shinagawa\\nJNCI 2022\\nCDC/NCHS 2021\\nAsians are the most rapidly growing racial/ethnic group in the US\\nFrom U.S. Census\",\n        \"last_edit_date\"\n\"2024-10-30T00:00:00\",\n        \"url\"\n\"https://canvas.stanford.edu/courses/198463/files?preview=14191559\",\n        \"num_tokens\"\n0,\n        \"block_metadata\"\n{\n            \"author\"\n\"Jeffrey Velotta (MD, FACS)\",\n            \"slide_range\"\n\"Slide 10-17\"\n        \"citation\"\n\"Slides 10-17, Lecture 5\"\n }\n    }, {\n        \"document_title\"\n\"Lectures\",\n        \"section_title\"\n\"Lecture 5\",\n        \"content\"\n\"I have no family history. I never smoked, and the lung lesion was picked up on a chest X-ray that I did for positive PPD. The final pathology revealed that the cancer has spread to the methastinum, giving me a stage IIIA diagnosis. I underwent lobectomy, radiation, chemotherapy, as well as oxymetinib, a targeted therapy for 3 years, which I finished in, uh, end of 2023. Uh, in May of this year, uh, I underwent surveillance, and the cancer has recurred and has spread to the spine and also the left adrenal gland. Uh, I was put back on a regimen consisting of targeted therapy as well as chemotherapeutic agents. Uh, I want to share this story with you, uh, to increase awareness. I was shocked by the experience. I was shocked a lot because I developed cancer. I was shocked because I am I I never smoke. I'm totally asymptomatic, and I don't have any family history, and I'm diagnosed to have lung cancer. Thank you for your attention. My lung cancer was detected instantly during a workup for fishbone. What happened was 3 months ago. I had persistent right neck pain for 10 days. I remember that I swallowed fishbone about 10 days ago. Since I'm radiologist, I went to get neck x-ray to look for fishbone.\",\n        \"last_edit_date\"\n\"2024-10-30T00:00:00\",\n        \"url\"\n\"https://mediasite.stanford.edu/Mediasite/Play/f6963fafb2f54cebb88957090a4785951d\",\n        \"num_tokens\"\n0,\n        \"block_metadata\"\n{\n            \"time_range_minutes\"\n\"32-37\",\n            \"speakers\"\n\"Jeffrey Velotta (MD, FACS), Bryant Lin (MD)\",\n            \"lecture_title\"\n\"Epidimeology and Cultural Considerations\"\n        \"citation\"\n\"Lecture 5, Epidimeology and Cultural Considerations\"}\n    }]"
        prompt = (
            f"You are a chatbot answering medical student questions about MED 275, a lung cancer course taught by Prof. Bryant Lin at Stanford University.\n"
            f"Your answers should be detailed and should use the provided Context and Previous Conversation History to answer the User Question.\n"
            f"If the context does not explicitly contain all the necessary information to answer the query, infer the best possible answer based on the provided information.\n"
            f"Do not create new information outside the scope of the provided context, but feel free to synthesize insights if relevant.\n\n"
            f"If the context contains no implicitly or explicitly relevant information to the user query, respond only with 'I'm sorry, I don't have enough information on that topic.'\n"
            f"Where applicable, suggest additional resources, such as course material, relevant URLs, or further steps the user might take.\n\n"
            f"Lectures are 60 minutes long, use the start and end times of lecture in the context to answer questions about time.\n"
            f"Cite the source used to generate each sentence in the response by adding the citation from the relevant document metadata in parenthesis after the sentence.\n"
            f"Do not mention that you used the context in your answer.\n\n"
            f"Vary your answer from previous responses, and avoid repeating information in Previous Conversation History.\n\n"
            #f"When generating a response, ensure that each sentence derived from a document is immediately followed by its corresponding citation in parentheses. Use the 'citation' field provided in the document metadata for the citation. If a sentence combines information from multiple documents, include citations for all relevant sources. For example, if the information comes from 'Lecture 5,' the citation should be formatted as (Lecture 5, Epidemiology and Cultural Considerations). Make sure the citations follow these rules consistently throughout the response."
            # f"If citing a lecture, include the start and end time and the unit of time minutes of the part of the lecture you are citing.\n\n"
            f"Previous Conversation History:\n{prev_context}\n\n"
            f"User Question:\n{user_query}\n\n"
            f"Context:\n{documents_context}\n\n"
            f"Answer:"
        )
        # Generate a response using the Together API
        response = self._together_generation_long(prompt)
        return response

    def clear_queue_and_prev_context(self):
        self.documents_queue.clear()
        self.prev_context = ""

    def get_response(self, user_query):
        # Potential fail cases: querying with time range of lecture, asking for recommendations -> should lead to graceful failure or cite additional resources,
        # asking about a lecture that doesn't exist
        if user_query == "":
            return "Please enter a question or type 'exit' to quit."

        # Fetch relevant documents using RAG
        fetch = self._fetch_from_rag(user_query)
        if len(fetch) > 0:
            documents = fetch[0]["results"]
            self.documents_queue.append(documents)
            if len(self.documents_queue) > 3: # TODO: potentially increase length of queue
                self.documents_queue.popleft()
        
        documents_list = []
        for item in self.documents_queue:
            if len(item) > 0:
                for document in item:
                    document.pop("similarity_score", None)
                    document.pop("probability_score", None)
                documents_list.extend(item)

        response = self._generate_response_with_llm(user_query, json.dumps(documents_list, indent=4, separators=(",\n")), self.prev_context)
        self.prev_context += "\nQuery: {}, Response: {}".format(user_query, response)
        return f"{response}"