# Auto Evaluator for Med 275 chatbot
from web_chatbot_v4 import Chatbot_v4
from web_chatbot_v5 import Chatbot_v5  
from web_chatbot_v6 import Chatbot_v6
from web_chatbot_timetest import Chatbot_v7
from basic_chatbot import BasicChatbot
import os

os.environ["TOGETHER_API_KEY"] = "30cde163d78fa4c02d653ab94957386b6dcfb1c370e2a04c8678dc17197794e1"

chatbot_v4 = Chatbot_v4(api_key=os.environ["TOGETHER_API_KEY"]) 
chatbot_v5 = Chatbot_v5(api_key=os.environ["TOGETHER_API_KEY"])
chatbot_v6 = Chatbot_v6(api_key=os.environ["TOGETHER_API_KEY"])
chatbot_v7 = Chatbot_v7(api_key=os.environ["TOGETHER_API_KEY"])
basic_chatbot = BasicChatbot(api_key=os.environ["TOGETHER_API_KEY"])

# from https://github.com/langchain-ai/auto-evaluator/blob/main/api/text_utils.py
template = """You are a teacher grading a quiz. 
You are given a question, the student's answer, and the true answer, and are asked to score the student answer as either Correct or Incorrect.
Grade the student answers based ONLY on their factual accuracy. Ignore differences in punctuation and phrasing between the student answer and true answer. It is OK if the student answer contains more information than the true answer or some of the information from the true answer, as long as it does not contain any conflicting statements. If the student answers that it is outside of their  knowledge capabilities, then the answer is Incorrect. Begin! 

QUESTION: {query}
STUDENT ANSWER: {result}
TRUE ANSWER: {answer}

Your response should be as follows:

GRADE: (Correct or Incorrect)
(line break)
JUSTIFICATION: (Without mentioning the student/teacher framing of this prompt, explain why the STUDENT ANSWER is Correct or Incorrect. Use one or two sentences maximum. Keep the answer as concise as possible.)
"""

def evaluate(file_name, queries, true_answers, chatbot):
    with open(file_name, "w") as file:
        for i in range(len(queries)):
            print(i,"out of", len(queries) - 1)
            if queries[i] == "clear":
                chatbot.clear_queue_and_prev_context()
                continue
            bot_answer = chatbot.get_response(queries[i])
            prompt = template.format(query=queries[i], result=bot_answer, answer=true_answers[i])
            grade = chatbot._together_generation_eval(prompt)
            file.write("bot_answer:" + bot_answer + "\n")
            file.write("grade:" + grade + "\n") 

queries = [
"Give me a summary of the class.",
"What is discussed in the first half of lecture 1?",
"What is discussed at the end of lecture 1?",
"clear",
"How do doctors diagnose lung cancer?",
"What are some of the difficulties with this?",
"clear",
"What are the top three treatments for never-smoker lung cancer?",
"Tell me more about each of them.",
"clear",
"Tell me about the readings in this class.",
"clear",
"Which population is most at risk for developing never smoker lung cancer?",
"clear",
"Give me a summary of lecture 2."
]

true_answers = [
"The class is a lung cancer course taught by Professor Bryant Lin at Stanford University. The lectures cover various topics related to lung cancer, such as diagnosis and screening, nutrition during cancer treatment, and culturally attuned interventions to support caregiving in cancer. The course has a unique format, with the professor sharing his personal experiences and insights as a cancer patient, and featuring guest speakers from various fields",
"The first half of Lecture 1 covers the introduction to the class, the logistics of the course, and the discussion of why the instructor, Bryant Lin, decided to start the class. The instructor introduces himself and the teaching assistants, discusses the format of the class, and explains the importance of attendance and participation. He also shares his personal experience with lung cancer and how it led him to create the class. The first half of the lecture also includes a discussion on the rapid progression of the disease and the challenges of navigating the healthcare system.",
"The end of lecture 1 discusses the risk factors of lung cancer, specifically in Asian populations. It also discusses the importance of lung cancer screening, specifically how lung cancer screening using low-dose CT (LDCT) scans is recommended for high-risk individuals. It discusses the findings of the NLST study, which demonstrated that LDCT scans reduced lung cancer mortality by 20%.",
"clear",
"Doctors diagnose lung cancer using methods such as low-dose computed tomography (LDCT) scans, chest X-rays, and biopsies. The Lung-RADS system classifies lung nodules by suspiciousness, guiding follow-up actions like repeat LDCT scans, PET CT scans, biopsies, or surgery. Screening programs, like the National Lung Screening Trial, have utilized LDCT scans to detect lung cancer in high-risk individuals. However, diagnosis can be challenging due to non-specific clinical presentations, underscoring the need for improved clinical quality measures to enhance diagnostic timeliness (Suchsland et al., 2022).",
"Diagnosing lung cancer is challenging due to its non-specific clinical presentation, which often delays early detection. Screening programs face additional obstacles, including risks such as radiation exposure, false positives, overdiagnosis, incidental findings, and patient anxiety. Despite these programs, uptake remains low, with only 16-17 percent of eligible individuals in California undergoing screening. Barriers to early diagnosis include patient and caregiver perceptions, healthcare system factors, and tumor characteristics, all of which contribute to delays in treatment and adversely affect survival rates (Suchsland et al., 2022; Cassim et al., 2019).",
"clear",
"The top three treatments for non-smoker lung cancer are:1. Targeted therapy with Epidermal Growth Factor Receptor (EGFR) tyrosine kinase inhibitors (TKIs), such as gefitinib, erlotinib, and afatinib, for patients with EGFR sensitizing mutations.2. Immunotherapy with immune checkpoint blockade targeting the programmed-death 1/programmed-death ligand 1 (PD-1/PD-L1) axis, such as pembrolizumab, for patients with advanced NSCLC and PD-L1 positive tumors.3. Anaplastic lymphoma kinase (ALK) inhibitors, such as crizotinib and alectinib, for patients with ALK rearrangements.These treatments are specifically targeted at patients with adenocarcinoma, a type of non-small cell lung cancer that is more common in never-smokers. It's worth noting that the effectiveness of these treatments may vary depending on the specific characteristics of the patient and the tumor, and that other treatments, such as chemotherapy and surgery, may also be used in certain cases. (Lung cancer in never smokers—the East Asian experience, 2018; LoPiccolo et al, 2024)Note: The use of targeted therapies may vary based on genetic mutations and biomarkers.",
"Here's more information about each of the top three treatments:1. Targeted therapy with Epidermal Growth Factor Receptor (EGFR) tyrosine kinase inhibitors (TKIs), such as gefitinib, erlotinib, and afatinib, for patients with EGFR sensitizing mutations. EGFR mutations are the most common driver gene found in never-smoker adenocarcinoma from East Asia, constituting 60-78 percent of this subgroup. Robust evidence has identified EGFR sensitizing mutation as the most relevant predictor of response to the EGFR tyrosine kinase inhibitors (EGFR-TKIs). Several randomized phase III trials have consistently demonstrated that gefitinib, erlotinib and afatinib are more effective in terms of objective response rate (ORR) and progression-free survival (PFS), and better tolerated than standard platinum-based doublet chemotherapy in advanced NSCLC patients harboring EGFR activating mutation. (Lung cancer in never smokers—the East Asian experience, 2018)2. Immunotherapy with immune checkpoint blockade targeting the programmed-death 1/programmed-death ligand 1 (PD-1/PD-L1) axis, such as pembrolizumab, for patients with advanced NSCLC and PD-L1 positive tumors. Immunotherapy with immune checkpoint blockade targeting the PD-1/PD-L1 axis represents a novel approach for the treatment of patients with advanced NSCLC. Several randomized trials have demonstrated a significant survival advantage of PD-1/PD-L1 antibodies over docetaxel as second-line therapy. Furthermore, pembrolizumab has been approved as first-line therapy for advanced NSCLC patients with PD-L1 positive tumors (>50%) based on the results of KEYNOTE-024 trial. (Lung cancer in never smokers—the East Asian experience, 2018)3. Anaplastic lymphoma kinase (ALK) inhibitors, such as crizotinib and alectinib, for patients with ALK rearrangements. ALK rearrangement defines another distinct subtype of patients with NSCLC, accounting for about 5% of all NSCLC cases. Crizotinib is an oral small-molecule TKI of ALK, MET, and ROS1 kinases and has been approved for the first-line treatment of advanced ALK-rearranged NSCLC based on the results from PROFILE1014 trial.",
"clear",
"The readings for MED 275 explore key challenges in cancer care, including the impact of language barriers on patients’ access to treatment, barriers to early diagnosis, and the timeliness of lung cancer diagnosis in clinical settings. Articles like 'Hidden Disparities: How Language Influences Patients’ Access to Cancer Care' by Chen et al. (2023) examine how language differences can lead to disparities in accessing cancer care services, highlighting systemic inequities and potential areas for intervention. Similarly, 'Patient and Carer Perceived Barriers to Early Presentation and Diagnosis of Lung Cancer: A Systematic Review' by Cassim et al. (2019) delves into obstacles faced by patients and caregivers that delay seeking care or receiving a timely diagnosis. 'How Timely Is Diagnosis of Lung Cancer? Cohort Study of Individuals with Lung Cancer Presenting in Ambulatory Care in the United States' by Suchsland et al. (2022) evaluates the speed and efficiency of diagnosing lung cancer in ambulatory care settings, offering insights into gaps in the healthcare system. For further reading, consider 'Lung cancer in patients who have never smoked — an emerging disease' by LoPiccolo et al.  (LoPiccolo et al, 2024). Together, these readings provide a comprehensive look at the intersection of healthcare access, systemic barriers, and diagnostic timeliness in oncology.",
"clear",
"Women who have never smoked are more than twice as likely to develop lung cancer than men who have never smoked (LoPiccolo et al, 2024). The proportion of lung cancers attributable to tobacco smoking varies across countries, with a higher proportion of lung cancers occurring in never-smokers in East Asia (Lung cancer in never smokers—the East Asian experience, 2018).",
"clear",
"I'm sorry, I don't have enough information on that topic."
]


i = 4
# evaluate("basic_eval" + str(i) + ".txt", queries, true_answers, basic_chatbot)
# evaluate("v4_eval" + str(i) + ".txt", queries, true_answers, chatbot_v4)
# evaluate("v5_eval" + str(i) + ".txt", queries, true_answers, chatbot_v5)
evaluate("v6_eval" + str(i) + ".txt", queries, true_answers, chatbot_v6)
# evaluate("v7_eval" + str(i) + ".txt", queries, true_answers, chatbot_v7)