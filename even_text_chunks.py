import os
import json

# Number of chars, about 200 words 
text_chunk_size = 1200

# Define the directory and file name
input_directory = 'cs224v-lecture-chatbot/audio_transcriptions'  
output_directory = 'cs224v-lecture-chatbot/chunked_transcriptions'

def sec_to_min(seconds):
    minutes = seconds // 60
    r_seconds = seconds % 60
    total_minutes = minutes + (0.01 * r_seconds)
    return round(total_minutes, 2)

for filename in os.listdir(input_directory):
    input_file_path = os.path.join(input_directory, filename)
    
    # Check if it is a file (and not a directory)
    if not os.path.isfile(input_file_path):
        raise ValueError("Input file not found: " + input_file_path)

    # Open and read the JSON file
    with open(input_file_path, 'r') as file:
        data = json.load(file)
    new_list = []
    i = 0
    new_i = 0
    while i < len(data):
        if len(new_list) == 0:
            new_list.append({"start": sec_to_min(data[i]["start"]), "end": data[i]["end"], "num_words": data[i]["num_words"], "speakers": set(data[i]["speakers"]), "text": data[i]["text"]})
            continue
        new_len = len(new_list[new_i]["text"])
        cur_len = len(data[i]["text"])
        if  new_len < text_chunk_size and new_len + cur_len < text_chunk_size + 50:
            new_list[new_i]["text"] = new_list[new_i]["text"] + " " + data[i]["text"]
            new_list[new_i]["end"] = data[i]["end"]
            new_list[new_i]["num_words"] = new_list[new_i]["num_words"] + data[i]["num_words"]
            new_list[new_i]["speakers"].add(data[i]["speakers"][0])
        else:
            new_list[new_i]["speakers"] = list(new_list[new_i]["speakers"])
            new_list[new_i]["end"] = sec_to_min(new_list[new_i]["end"])
            new_list.append({"start": sec_to_min(data[i]["start"]), "end": data[i]["end"], "num_words": data[i]["num_words"], "speakers": set(data[i]["speakers"]), "text": data[i]["text"]})
            new_i += 1
        i += 1

    # Handle the last one
    if new_i < len(new_list):
        new_list[new_i]["speakers"] = list(new_list[new_i]["speakers"])
        new_list[new_i]["end"] = sec_to_min(new_list[new_i]["end"])

    output_file_path = os.path.join(output_directory, filename)
    with open(output_file_path, 'w') as file:
        json.dump(new_list, file, indent=4)
    
