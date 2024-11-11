import json
import os
import re
import math

INPUT_DIR = "chunked_audio_transcriptions_even"
OUTPUT_DIR = "chunked_audio_transcriptions_even"

# Set default metadata
TITLE = "Lectures"
LANGUAGE = "en"

lectures = {
    "MED-275_09-25-2024-0_transcription_output.json": {
        "last_edit_date": "2024-09-25",
        "lecture_title": "Diagnosis and Screening",
        "lecture_num": 1,
        "url": "https://mediasite.stanford.edu/Mediasite/Play/069f043e54e84dadb2d0637e6b6df1cd1d",
        "speakers": ["Bryant Lin (MD)", "Natalie Liu (MD)"]
    },
    "MED-275_10-09-2024-0_transcription_output.json": {
        "last_edit_date": "2024-10-09",
        "lecture_num": 3,
        "url": "https://mediasite.stanford.edu/Mediasite/Play/2adbb17b399b417ca7e30245df55c3361d",
        "speakers": ["Bryant Lin (MD)"]
    },
    "MED-275_10-16-2024-0_transcription_output.json": {
        "last_edit_date": "2024-10-16",
        "lecture_title": "Developing Culturally Attuned Interventions to Support Caregiving in Cancer",
        "lecture_num": 4,
        "url": "https://mediasite.stanford.edu/Mediasite/Play/f92af043a02844109253875ab70d0f051d",
        "speakers": ["Ranak Trivedi (PhD, FSBM, FGSA)", "Bryant Lin (MD)"]
    },
    "MED-275_10-30-2024-0_transcription_output.json": {
        "last_edit_date": "2024-10-30",
        "lecture_title": "Epidimeology and Cultural Considerations",
        "lecture_num": 5,
        "url": "https://mediasite.stanford.edu/Mediasite/Play/f6963fafb2f54cebb88957090a4785951d",
        "speakers": ["Jeffrey Velotta (MD, FACS)", "Bryant Lin (MD)"]
    },
    "MED-275_11-06-2024-0_transcription_output.json": {
        "last_edit_date": "2024-11-06",
        "lecture_title": "Nutrition During Cancer Treatment",
        "lecture_num": 6,
        "url": "https://mediasite.stanford.edu/Mediasite/Play/ca12283fe2ff4f90bccea88816ab19a91d",
        "speakers": ["Kate Donelan (MS, RD)", "Bryant Lin (MD)"]
    }
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
    url = lectures[lecture]["url"]
    speakers = lectures[lecture]["speakers"]
    for item in lecture_json:
        entry = {
            "document_title": TITLE,
            "section_title": f"{TITLE} > Lecture {lecture_num}",
            "content": item["text"],
            "last_edit_date": lecture_date,
            "url": url,
            "block_metadata": {
                "block_type": "text",
                "language": LANGUAGE,
                "time_range_minutes": f"{math.floor(item['start'])}-{math.ceil(item['end'])}",
                "speakers": speakers
            }
        }
        if lecture_title:
            entry["block_metadata"]["lecture_title"] = lecture_title
        json_lines.append(entry)

# Define output file path and write JSON lines format data
output_file = os.path.join(OUTPUT_DIR, "lectures.jsonl")
with open(output_file, "w") as json_file:
    for entry in json_lines:
        json.dump(entry, json_file, ensure_ascii=False)
        json_file.write("\n")
