import scipdf
import json
import glob
import os
import re

INPUT_DIR = "text_files"
OUTPUT_DIR = "chunked_text_transcriptions_scipdf"

# Set default metadata
TITLE = "Readings"
LANGUAGE = "en"

readings = {
    "10-9-24 cancers-14-05756.pdf": {
        "name": "How Timely Is Diagnosis of Lung Cancer? Cohort Study of Individuals with Lung Cancer Presenting in Ambulatory Care in the United States (Suchsland et al)",
        "last_edit_date": "2022-11-23",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC9740627"
    },
    "10-9-24 jnccn-article-p951.pdf": {
        "name": "Hidden Disparities: How Language Influences Patients’ Access to Cancer Care (Chen et al)",
        "last_edit_date": "2023-09-01",
        "url": "https://jnccn.org/view/journals/jnccn/21/9/article-p951.xml"
    },
    "10-9-24 s12885-018-5169-9.pdf": {
        "name": "Patient and carer perceived barriers to early presentation and diagnosis of lung cancer: a systematic review (Cassim et al)",
        "last_edit_date": "2019-01-08",
        "url": "https://pubmed.ncbi.nlm.nih.gov/30621616/"
    },
    "MED 275 Syllabus_ From Diagnosis to Dialogue_ A Doctor's Real-Time Battle with Cancer.pdf": {
        "name": "MED 275 Syllabus: From Diagnosis to Dialogue: A Doctor's Real-Time Battle with Cancer",
        "last_edit_date": "2024-10-30",
        "url": "https://canvas.stanford.edu/courses/198463/files?preview=14191550"
    },
    "nihms-1977779.pdf": {
        "name": "Lung cancer in patients who have never smoked — an emerging disease (LoPiccolo et al)",
        "last_edit_date": "2024-01-09",
        "url": "https://www.nature.com/articles/s41571-023-00844-0"
    },
    "Serious-Illness-Conversation-Guide.pdf": {
        "name": "Serious Illness Conversation Guide",
        "last_edit_date": "2023-05-01",
        "url": "https://canvas.stanford.edu/courses/198463/files?preview=13816482"
    },
    "tlcr-07-04-450.pdf": {
        "name": "Lung cancer in never smokers—the East Asian experience",
        "last_edit_date": "2018-08-17",
        "url": "https://pubmed.ncbi.nlm.nih.gov/30225210/"
    }
}
# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Regular expression to split text by paragraph
paragraph_endings = re.compile(r'\n')
json_lines = []
for reading in readings:
    pdf_file = os.path.join(INPUT_DIR, reading)
    article_dict = scipdf.parse_pdf_to_dict(pdf_file, as_list=False)  # return dictionary
    sections = article_dict["sections"]
    
    if article_dict.get("abstract"):
        abstract = article_dict["abstract"]
        entry = {
            "document_title": TITLE,
            "full_section_title": f"{TITLE} > {readings[reading]['name']} > Abstract",
            "content": abstract,
            "block_type": "text",
            "language": LANGUAGE,
            "last_edit_date": readings[reading]["last_edit_date"],
            "url": readings[reading]["url"]
        }
        json_lines.append(entry)

    cleaned_sections = []

    for section in sections:
        heading = section["heading"]
        text = section["text"]
        for i in range(max(-len(cleaned_sections), -5), 0):
            cleaned_section = cleaned_sections[i]
            if section["heading"] == cleaned_section["heading"] and section["text"].startswith(cleaned_section["text"]):
                del cleaned_sections[i]
        cleaned_sections.append(section)

    for section in cleaned_sections:
        heading = section["heading"]
        text = section["text"]
        
        if len(text.strip()) > 0:
            # Split text into sentences using regex
            paragraphs = paragraph_endings.split(text.strip())
            chunks = []
            current_chunk = []
            current_chunk_word_count = 0
            
            for paragraph in paragraphs:
                paragraph_word_count = len(paragraph.split())
                
                # Check if adding this sentence would make the chunk too large
                if current_chunk_word_count + paragraph_word_count > 400:
                    # Append current chunk to chunks list and reset
                    chunks.append((current_chunk_word_count, " ".join(current_chunk)))
                    current_chunk = []
                    current_chunk_word_count = 0

                # Add sentence to the current chunk
                current_chunk.append(paragraph)
                current_chunk_word_count += paragraph_word_count

            # Append any remaining sentences as the last chunk
            if current_chunk:
                chunks.append((current_chunk_word_count, " ".join(current_chunk)))

            # Balance the last chunk if it's too short compared to the average
            # while len(chunks) > 1 and chunks[-1][0] < 200:
            #     last_chunk_words, last_chunk_text = chunks.pop()
            #     chunks[-1] = (
            #         chunks[-1][0] + last_chunk_words, 
            #         chunks[-1][1] + " " + last_chunk_text
            #     )

            # Construct metadata fields
            full_section_title = f"{TITLE} > {heading if heading else 'Section'}"
            
            # Add the final balanced chunks to json_lines
            for idx, (word_count, chunk_text) in enumerate(chunks):
                if word_count > 0:
                    entry = {
                        "document_title": TITLE,
                        "full_section_title": f"{TITLE} > {readings[reading]['name']} > {heading if heading else 'Section'}",
                        "content": chunk_text,
                        "block_type": "text",
                        "language": LANGUAGE,
                        "last_edit_date": readings[reading]["last_edit_date"],
                        "url": readings[reading]["url"]
                    }
                    json_lines.append(entry)

# Define output file path and write JSON lines format data
output_file = os.path.join(OUTPUT_DIR, "readings.jsonl")
with open(output_file, "w") as json_file:
    for entry in json_lines:
        json.dump(entry, json_file, ensure_ascii=False)
        json_file.write("\n")
