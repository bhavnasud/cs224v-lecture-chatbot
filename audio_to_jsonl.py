import scipdf
import json
import glob
import os
import re

INPUT_DIR = "chunked_audio_transcriptions_even"
OUTPUT_DIR = "chunked_audio_transcriptions_even"

# Set default metadata
TITLE = "Lectures"
LANGUAGE = "en"

lectures = {
    "MED-275_09-25-2024-0_transcription_output.json": {
        "last_edit_date": "2024-09-25",
        "lecture_title": "Diagnosis and Screening",
        "lecture_num": 1
    },
    "MED-275_10-09-2024-0_transcription_output.json": {
        "last_edit_date": "2024-10-09",
        "lecture_num": 3
    },
    "MED-275_10-16-2024-0_transcription_output.json": {
        "last_edit_date": "2024-10-16",
        "lecture_title": "Developing Culturally Attuned Interventions to Support Caregiving in Cancer",
        "lecture_num": 4
    },
}

# Regular expression to split text by paragraph
paragraph_endings = re.compile(r'\n')
json_lines = []
for lecture in lectures:
    lecture_json_file = os.path.join(INPUT_DIR, lecture)
    lecture_json = {}
    with open(lecture_json_file) as f:
        lecture_json = json.load(f)
    lecture_num = lectures[lecture]["lecture_num"]
    lecture_date = lectures[lecture]["last_edit_date"]
    lecture_title = lectures[lecture].get("lecture_title")
    for item in lecture_json:
        entry = {
            "document_title": TITLE,
            "full_section_title": f"{TITLE} > Lecture {lecture_num}",
            "content": item["text"],
            "block_type": "text",
            "language": LANGUAGE,
            "last_edit_date": lecture_date,
        }
        if lecture_title:
            entry["full_section_title"] += f" ({lecture_title})"
        json_lines.append(entry)

# Define output file path and write JSON lines format data
output_file = os.path.join(OUTPUT_DIR, "lectures.jsonl")
with open(output_file, "w") as json_file:
    for entry in json_lines:
        json.dump(entry, json_file, ensure_ascii=False)
        json_file.write("\n")
