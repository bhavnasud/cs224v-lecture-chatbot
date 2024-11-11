import json

def remove_key_from_jsonl(input_file, output_file, key_to_remove):
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        for line in infile:
            # Parse each line as a JSON object
            entry = json.loads(line)
            
            # Remove the specified key if it exists
            if key_to_remove in entry:
                del entry[key_to_remove]
            
            # Write the modified entry to the output file
            outfile.write(json.dumps(entry) + '\n')

# Specify the input file, output file, and the key to remove
input_file = 'chunked_text_transcriptions_scipdf/cleaned_readings.jsonl'
output_file = 'chunked_text_transcriptions_scipdf/cleaned_readings_2.jsonl'
key_to_remove = 'num_words'

remove_key_from_jsonl(input_file, output_file, key_to_remove)