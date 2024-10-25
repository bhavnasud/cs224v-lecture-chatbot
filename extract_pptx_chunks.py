import json
from pptx import Presentation
import glob

INPUT_DIR = "slides"
OUTPUT_DIR = "chunked_slide_transcriptions"


def pptx_to_json(pptx_file, json_file):
    # Load the presentation
    presentation = Presentation(pptx_file)
    
    # Initialize the list to hold slide data
    slides_data = []

    # Iterate through each slide in the presentation
    for slide in presentation.slides:
        slide_text = []
        
        # Collect all text in the slide
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                slide_text.append(shape.text)
        
        # Join all text into a single string
        text = "\n".join(slide_text)
        num_words = len(text.split())
        
        # Append slide data to the list
        slides_data.append({"num_words": num_words, "text": text})

    # Write the data to a JSON file
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(slides_data, f, ensure_ascii=False, indent=4)

for pptx_file in glob.glob(INPUT_DIR + "/*.pptx"):
    print("processing file ", pptx_file)
    output_file = pptx_file.replace(".pptx", "_transcription_output.json").replace(INPUT_DIR, OUTPUT_DIR)
    pptx_to_json(pptx_file, output_file)
    print(f"Data successfully saved to {output_file}")
    