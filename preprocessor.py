from html_processor import HTMLProcessor
from os import path
import os
from annotate import annotate_text
import json
from tqdm import tqdm

OUTPUT_FILE_PATH = os.path.join("configs", "prompts.json")
url = "https://www.ncbi.nlm.nih.gov/books/NBK1124/?report=printable"

# STEP 1: Preprocess html
noonan_gene_reviews = HTMLProcessor(url)
partitions = noonan_gene_reviews.split_html("h2", avoid_tags=["h2", "h3", "h4"])

# STEP 2: Run html partitions through FastHPOCR
HPO_INDEX_DIR = path.join(os.getcwd(), "hpo_index", "hp.index")
results = []  # List to store the tuples

for text in tqdm(partitions):
    hpo_result = annotate_text(HPO_INDEX_DIR, text, print_result=False)

    if hpo_result:
        text = text.replace('"', '\\"')
        results.append((text, hpo_result))
        # TODO: Validate these results
    else:
        print(f"No HPO result for text: \n{text}") 
        # TODO: Validate these results
prompt_list = []

with open("configs/prompt_template.json", "r") as prompt_file:
    prompt_template = prompt_file.read()

for text, hpo_result in results:
    # Create a fresh copy of the template string
    modified_prompt_str = prompt_template

    # Replace placeholders with actual values
    modified_prompt_str = modified_prompt_str.replace("{{hpo_terms}}", hpo_result)
    modified_prompt_str = modified_prompt_str.replace("{{clinical_text}}", text)

    try:
        modified_prompt = json.loads(modified_prompt_str, strict=False)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        print(f"Problematic JSON string: {modified_prompt_str}")

    # Append the modified prompt array to the list
    prompt_list.append(modified_prompt)

print(f"{len(prompt_list)} prompts generated.")
# Convert the modified data to a JSON string with indentation for readability
output_str = json.dumps(prompt_list, indent=4)
# Save the modified JSON string to the specified path
with open(OUTPUT_FILE_PATH, "w") as output_file:
    output_file.write(output_str)
