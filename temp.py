import json

with open('bard_response.jsonl', 'r') as f, open('your_file_temp.jsonl', 'w') as out:
    for line in f:
        json_obj = json.loads(line)
        if "error" not in json_obj["predicted_answer"]:
            out.write(line)

# after writing all the lines to the new file, remove the original file and rename the new file
import os
os.remove('bard_response.jsonl')
os.rename('your_file_temp.jsonl', 'bard_response.jsonl')
