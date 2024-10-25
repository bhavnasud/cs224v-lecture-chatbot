import os
import json

# Number of chars, about 200 words 
text_chunk_size = 1200

# Define the directory and file name
input_directory = 'chunked_text_transcriptions'  
output_directory = 'chunked_text_transcriptions_even'

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
            new_list.append({"num_words": data[i]["num_words"], "text": data[i]["text"]})
            continue
        new_len = len(new_list[new_i]["text"])
        cur_len = len(data[i]["text"])
        if  new_len < text_chunk_size and new_len + cur_len < text_chunk_size + 50:
            new_list[new_i]["text"] = new_list[new_i]["text"] + " " + data[i]["text"]
            new_list[new_i]["num_words"] = new_list[new_i]["num_words"] + data[i]["num_words"]
        else:
            new_list.append({"num_words": data[i]["num_words"], "text": data[i]["text"]})
            new_i += 1
        i += 1

    output_file_path = os.path.join(output_directory, filename)
    with open(output_file_path, 'w') as file:
        json.dump(new_list, file, indent=4)
    
