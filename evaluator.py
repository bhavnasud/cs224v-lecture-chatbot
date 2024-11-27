# Auto Evaluator for Med 275 chatbot
from web_chatbot_v4 import Chatbot_v4
from web_chatbot_v5 import Chatbot_v5  
from basic_chatbot import BasicChatbot
import os

os.environ["TOGETHER_API_KEY"] = "30cde163d78fa4c02d653ab94957386b6dcfb1c370e2a04c8678dc17197794e1"

# Initialize your chatbot with the API key
chatbot_v4 = Chatbot_v4(api_key=os.environ["TOGETHER_API_KEY"]) 
chatbot_v5 = Chatbot_v5(api_key=os.environ["TOGETHER_API_KEY"])
basic_chatbot = BasicChatbot(api_key=os.environ["TOGETHER_API_KEY"])

# from https://github.com/langchain-ai/auto-evaluator/blob/main/api/text_utils.py
template = """You are a teacher grading a quiz. 
You are given a question, the student's answer, and the true answer, and are asked to score the student answer as either Correct or Incorrect.
Grade the student answers based ONLY on their factual accuracy. Ignore differences in punctuation and phrasing between the student answer and true answer. It is OK if the student answer contains more information than the true answer, as long as it does not contain any conflicting statements. If the student answers that there is no specific information provided in the context, then the answer is Incorrect. Begin! 

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
            # file.write("query:" + queries[i] + "\n") 
            # file.write("bot_answer:" + bot_answer + "\n")
            # file.write("true_answer:" + true_answers[i]+ "\n")
            grade = chatbot._together_generation_eval(prompt)
            file.write("grade:" + grade + "\n") 

queries = ["Give me a summary of the class", 
           "What is discussed in the beginning of lecture 1?", 
           "What is discussed at the end of lecture 1?", 
           "clear", 
           "How do doctors diagnose lung cancer?", 
           "Tell me more", 
           "clear", 
           "What are the top three treatments for lung cancer?", 
           "Tell me more about each of them", 
           "clear", 
           "Tell me about the readings in this class", 
           "clear",
           "Which population is most at risk for developing never smoker lung cancer?"]

true_answers = [
                "The class is a lung cancer course taught by Professor Bryant Lin at Stanford University. It is a 60-minute long course with lectures that cover various topics related to lung cancer, such as diagnosis and screening, nutrition during cancer treatment, and culturally attuned interventions to support caregiving in cancer. The course has a unique format, with the professor sharing his personal experiences and insights as a cancer patient, and featuring guest speakers from various fields. The class also includes interactive elements, such as writing down three good things that happened in the day, and has a strong focus on community and support. The course is designed to be an once-in-a-lifetime opportunity for students to learn about lung cancer and its complexities.",
                "The beginning of lecture 1 covers the introduction to the class, including the logistics of attendance and assignments, and also discusses the importance of early diagnosis and staging of cancer, as well as lung cancer screening. (Lecture 1, 0-2 minutes, Lecture 1, 18-20 minutes)",
                "At the end of lecture 1, the speaker is concluding the introductory remarks, thanking the attendees for their patience and interest in the class, and introducing the topic of lung cancer diagnosis and screening, including the importance of early detection and the challenges of diagnosing lung cancer at an early stage. (Lecture 1, 52-60 minutes)",
                "clear",
                "Doctors can diagnose lung cancer using various methods, including low dose computed tomography (LDCT) scans, chest X-rays, PET CT scans, biopsies, and other diagnostic tests (Lecture 1, 39-41 minutes). However, a diagnosis is often delayed due to non-specific clinical presentations and the subtlety of lung cancer symptoms (Suchsland et al, 2022; Cassim et al, 2019). Healthcare providers may also face challenges in diagnosing lung cancer, including a lack of knowledge about interpreting symptoms and accessing appropriate treatment pathways (Cassim et al, 2019). It's essential for doctors to be vigilant and consider the possibility of lung cancer in patients who present with suspicious symptoms, especially those with a history of smoking or other risk factors.",
                "Lung cancer diagnosis is often delayed due to non-specific clinical presentations and the subtlety of lung cancer symptoms. According to Suchsland et al. (2022), the median interval from initial clinical presentation to chest CT or chest X-ray imaging is 291 days, and from initial clinical presentation to specialist visit is 236 days. Furthermore, the time interval from diagnosis to treatment initiation is typically short, with a median of 7 days. However, the duration from symptom onset to diagnosis is longer than most previous studies, exceeding World Health Organization targets and Canadian guidelines. (Suchsland et al, 2022)",
                "clear",
                "There are three main treatments: 1. Crizotinib, an oral small-molecule type II tyrosine kinase inhibitor (TKI) of ALK, MET, and ROS1 kinases, approved for the first-line treatment of advanced ALK-rearranged non-small cell lung cancer (NSCLC) [1]. 2. Alectinib, a highly selective ALK inhibitor with high brain-penetrant, which showed high anti-tumor activity both in ALK inhibitor-naive and crizotinib-resistant patients, and is considered a standard first-line therapy in some countries, such as China, Japan, and South Korea [2]. 3. Gefitinib, erlotinib, and afatinib, type I tyrosine kinase inhibitors (TKIs) of EGFR, which target EGFR mutations in NSCLC, and have shown effective and better tolerance than standard platinum-based doublet chemotherapy in several randomized phase III trials [3, 4, 5]. These treatments are specifically targeted at patients with adenocarcinoma, a type of non-small cell lung cancer that is more common in never-smokers.References: [1] Lung cancer in never smokers—the East Asian experience, 2018 [2] J-ALEX trial, ALEX trial, 2018, 2024 [3] NEJ002 trial, IPASS, LUX-LUNG 6 trial, First-SIGNAL trial, OPTIMAL, ENSURE, CONVINCE trial, WJTOG3405, 2018 Note: The use of targeted therapies may vary based on genetic mutations and biomarkers.",
                "Crizotinib, Alectinib, and Gefitinib, Erlotinib, and Afatinib are three treatments for lung cancer. Crizotinib is an oral small-molecule type II tyrosine kinase inhibitor (TKI) of ALK, MET, and ROS1 kinases, approved for the first-line treatment of advanced ALK-rearranged non-small cell lung cancer (NSCLC) (Lung cancer in never smokers—the East Asian experience, 2018). Alectinib is a highly selective ALK inhibitor with high brain-penetrant, which showed high anti-tumor activity both in ALK inhibitor-naive and crizotinib-resistant patients, and is considered a standard first-line therapy in some countries, such as China, Japan, and South Korea (J-ALEX trial, ALEX trial, 2018, 2024). Gefitinib, Erlotinib, and Afatinib are type I tyrosine kinase inhibitors (TKIs) of EGFR, which target EGFR mutations in NSCLC, and have shown effective and better tolerance than standard platinum-based doublet chemotherapy in several randomized phase III trials (NEJ002 trial, IPASS, LUX-LUNG 6 trial, First-SIGNAL trial, OPTIMAL, ENSURE, CONVINCE trial, WJTOG3405, 2018).",
                "clear",
                "The readings for this class focus on improving communication in healthcare and understanding barriers to early cancer diagnosis. The updated Serious Illness Conversation Guide by Ariadne Labs emphasizes inclusive, patient-tested language to facilitate meaningful discussions about care preferences and priorities for diverse patients with serious illnesses. Meanwhile, Cassim et al. (2019) highlights systemic and interpersonal barriers to early lung cancer diagnosis, including limited healthcare access and poor patient awareness, offering insights into improving early detection and patient outcomes. Both readings underline the importance of empathy, clarity, and accessibility in healthcare interactions.",
                "clear",
                "Women who have never smoked are more than twice as likely to develop lung cancer than men who have never smoked (LoPiccolo et al, 2024). The proportion of lung cancers attributable to tobacco smoking varies across countries, with a higher proportion of lung cancers occurring in never-smokers in East Asia (Lung cancer in never smokers—the East Asian experience, 2018)."
]

# evaluate("v4_eval.txt", queries, true_answers, chatbot_v4)
# evaluate("basic_eval.txt", queries, true_answers, basic_chatbot)
evaluate("v5_eval.txt", queries, true_answers, chatbot_v5)