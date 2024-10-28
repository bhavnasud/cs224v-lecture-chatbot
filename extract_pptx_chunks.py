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

    # Iterate through each slide in the presentation with their index
    for slide_index, slide in enumerate(presentation.slides, start=1):  # Start counting from 1
        slide_text = []
        
        # Collect all text in the slide, sorting shapes by their vertical position
        shapes_with_text = [
            shape for shape in slide.shapes if hasattr(shape, "text_frame")
        ]
        
        # Sort shapes by their top position (y-coordinate)
        shapes_with_text.sort(key=lambda s: s.top)

        # Collect text from sorted shapes
        for shape in shapes_with_text:
            for paragraph in shape.text_frame.paragraphs:
                paragraph_text = ''.join(run.text for run in paragraph.runs)
                if paragraph_text:  # Only add non-empty paragraphs
                    slide_text.append(paragraph_text)

        # Join all text into a single string
        text = "\n".join(slide_text)
        num_words = len(text.split())
        
        # Append slide data to the list with slide number
        slides_data.append({
            "slide_number": slide_index,
            "num_words": num_words,
            "text": text
        })

    # Write the data to a JSON file
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(slides_data, f, ensure_ascii=False, indent=4)

# Process each PowerPoint file in the input directory
for pptx_file in glob.glob(INPUT_DIR + "/*.pptx"):
    print("Processing file:", pptx_file)
    output_file = pptx_file.replace(".pptx", "_transcription_output.json").replace(INPUT_DIR, OUTPUT_DIR)
    pptx_to_json(pptx_file, output_file)
    print(f"Data successfully saved to {output_file}")