import os
import json
from deepgram import DeepgramClient, FileSource, PrerecordedOptions
import asyncio
import glob

# Path to the audio file
AUDIO_DIR = "audio_files"
OUTPUT_DIR = "audio_transcriptions"

# Get API key from environment variables
API_KEY = os.getenv("DEEPGRAM_API_KEY")

# Check if the API key is loaded correctly
if not API_KEY:
    raise ValueError("Deepgram API key is not set in environment variables.")

deepgram = DeepgramClient(API_KEY)

# Function to transcribe an audio file and save as JSON
async def transcribe_and_save(audio_file):
    output_file = audio_file.replace(".mp3", "_transcription_output.json").replace(AUDIO_DIR, OUTPUT_DIR)
    if os.path.exists(output_file):
        print("Transcribed file ", output_file, " already exists")
        return

    audio_data = None
    with open(audio_file, "rb") as audio:
        audio_data = audio.read()

    options = PrerecordedOptions(
        model="nova-2-medical", # TODO: also try enhanced-general
        smart_format=True,
        diarize=True,
        punctuate=True,
        filler_words=True,
        paragraphs=True
    )
    
    payload: FileSource = {
        "buffer": audio_data
    }

    # Get transcription response
    response = deepgram.listen.prerecorded.v("1").transcribe_file(payload, options, timeout=300)

    response_dict = json.loads(response.to_json())
    parsed_paragraphs = []
    for paragraph in response_dict['results']['channels'][0]['alternatives'][0]['paragraphs']['paragraphs']:
        parsed_paragraph = {
            "start": paragraph["start"],
            "end": paragraph["end"],
            "num_words": paragraph["num_words"],
            "speakers": [paragraph["speaker"]]
        }

        for sentence in paragraph["sentences"]:
            if "text" in parsed_paragraph:
                parsed_paragraph["text"] = parsed_paragraph["text"] + " " + sentence["text"]
            else:
                parsed_paragraph["text"] = sentence["text"]
        parsed_paragraphs.append(parsed_paragraph)

    with open(output_file, "w") as f:
        json.dump(parsed_paragraphs, f, indent=4)

    print(f"Transcription saved to {output_file}")

for audio_file in glob.glob(AUDIO_DIR + "/*.mp3"):
    asyncio.run(transcribe_and_save(audio_file))
