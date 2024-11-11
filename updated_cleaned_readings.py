import json

def update_jsonl(input_file, output_file, key_to_remove):
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        for line in infile:
            # Parse each line as a JSON object
            entry = json.loads(line)
            
            # Remove the specified key if it exists
            if key_to_remove in entry:
                del entry[key_to_remove]
            
            entry["section_title"] = entry["full_section_title"]
            del entry["full_section_title"]
            entry["block_metadata"] = {
                "block_type": entry["block_type"],
                "language": entry["language"]
            }
            del entry["block_type"]
            del entry["language"]
            # Write the modified entry to the output file
            outfile.write(json.dumps(entry) + '\n')


# Specify the input file, output file, and the key to remove
input_file = 'chunked_text_transcriptions_scipdf/cleaned_readings.jsonl'
output_file = 'chunked_text_transcriptions_scipdf/cleaned_readings_2.jsonl'
key_to_remove = 'num_words'

update_jsonl(input_file, output_file, key_to_remove)
