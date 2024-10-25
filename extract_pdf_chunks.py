
import glob
import PyPDF2
import json
import re

# Path to the audio file
INPUT_DIR = "text_files"
OUTPUT_DIR = "chunked_text_transcriptions"


def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, "rb") as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
    return text

def split_into_paragraphs(text):
    # Split by newlines and also consider line breaks and sentence-ending punctuation
    # This regex captures text that follows a newline, capitalized letters, and previous sentences that end with punctuation
    paragraphs = re.split(r'(?<=\.|\?|\!)\s*\n+', text.strip())
    
    # Clean up the resulting paragraphs
    processed_paragraphs = [para.strip() for para in paragraphs if para.strip()]
    
    return processed_paragraphs

def process_paragraphs(paragraphs):
    data = []
    for paragraph in paragraphs:
        # Replace internal newline characters with spaces
        paragraph = paragraph.replace('\n', ' ').encode('utf-8').decode('unicode_escape')
        paragraph = re.sub(r'[^\x00-\x7F]+', '', paragraph)
        # paragraph = re.sub(r'\\u[0-9]{4}', '', paragraph)
        num_words = len(paragraph.split())
        data.append({"num_words": num_words, "text": paragraph})
    return data

def save_to_json(data, json_path):
    with open(json_path, "w") as json_file:
        json.dump(data, json_file, indent=4)

for text_file in glob.glob(INPUT_DIR + "/*.pdf"):
    print("processing file ", text_file)
    text = extract_text_from_pdf(text_file)
    paragraphs = split_into_paragraphs(text)
    data = process_paragraphs(paragraphs)
    output_file = text_file.replace(".pdf", "_transcription_output.json").replace(INPUT_DIR, OUTPUT_DIR)
    save_to_json(data, output_file)
    print(f"Data successfully saved to {output_file}")
    