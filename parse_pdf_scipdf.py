import scipdf
import json
import glob
import os
import re

INPUT_DIR = "text_files"
OUTPUT_DIR = "chunked_text_transcriptions_scipdf"

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Regular expression to split text by sentence-ending punctuation (., ?, !)
sentence_endings = re.compile(r'(?<=[.!?])\s+')

for pdf_file in glob.glob(os.path.join(INPUT_DIR, "*.pdf")):
    article_dict = scipdf.parse_pdf_to_dict(pdf_file, as_list=False)  # return dictionary
    sections = article_dict["sections"]
    json_data = []
    
    for section in sections:
        heading = section["heading"]
        text = section["text"]
        
        if len(text) > 0:
            # Split text into sentences using regex
            sentences = sentence_endings.split(text)
            chunks = []
            current_chunk = []
            current_chunk_word_count = 0
            
            for sentence in sentences:
                sentence_word_count = len(sentence.split())
                
                # Check if adding this sentence would make the chunk too large
                if current_chunk_word_count + sentence_word_count > 200:
                    # Append current chunk to chunks list and reset
                    chunks.append((current_chunk_word_count, " ".join(current_chunk)))
                    current_chunk = []
                    current_chunk_word_count = 0

                # Add sentence to the current chunk
                current_chunk.append(sentence)
                current_chunk_word_count += sentence_word_count

            # Append any remaining sentences as the last chunk
            if current_chunk:
                chunks.append((current_chunk_word_count, " ".join(current_chunk)))

            # Balance the last chunk if it's too short compared to the average
            while len(chunks) > 1 and chunks[-1][0] < 100:
                last_chunk_words, last_chunk_text = chunks.pop()
                chunks[-1] = (
                    chunks[-1][0] + last_chunk_words, 
                    chunks[-1][1] + " " + last_chunk_text
                )

            # Add the final balanced chunks to json_data
            for idx, (word_count, chunk_text) in enumerate(chunks):
                json_data.append({
                    "num_words": word_count + (len(heading.split()) if idx == 0 and heading else 0),
                    "text": (f"{heading}: " if heading and idx == 0 else "") + chunk_text
                })

    # Define output file path and write JSON data
    output_file = os.path.join(OUTPUT_DIR, os.path.basename(pdf_file).replace(".pdf", "_transcription_output.json"))
    with open(output_file, "w") as json_file:
        json.dump(json_data, json_file, indent=4)