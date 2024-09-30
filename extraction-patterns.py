import argparse
from os import path
from html_processor import HTMLProcessor
from tqdm import tqdm

NOONAN_SYNDROME_DOC = path.join("Noonan-Syndrome-GeneReviews.html")
URL = "https://www.ncbi.nlm.nih.gov/books/NBK1124/?report=printable"
HPO_INDEX_DIR = path.join("hpo_index", "hp.index")

# Prompt templates
PHENOTYPE_EXTRACTION_TEMPLATE = path.join("prompt_templates/phenotype_extraction.json")
PHENOTYPE_FREQUENCY_EXTRACTION_PROMPT_TEMPLATE = path.join(
    "prompt_templates", "phenotype_frequency_extraction.json"
)
FREQUENCY_VALIDATION_PROMPT_TEMPLATE = path.join(
    "prompt_templates", "frequency_validation.json"
)
PHENOTYPE_ONSET_EXTRACTION_PROMPT_TEMPLATE = path.join(
    "prompt_templates", "phenotype_onset_extraction.json"
)
ONSET_VALIDATION_PROMPT_TEMPLATE = path.join(
    "prompt_templates", "onset_validation.json"
)

# Pipeline output directories
PHENOTYPE_FREQUENCY_WITH_FASTHPOCR_OUTPUTS_DIR = (
    "phenotype_frequency_with_FastHPOCR_pipeline_outputs"
)
PHENOTYPE_FREQUENCY_WITHOUT_FASTHPOCR_OUTPUTS_DIR = (
    "phenotype_frequency_without_FastHPOCR_pipeline_outputs"
)
PHENOTYPE_ONSET_WITH_FASTHPOCR_OUTPUTS_DIR = (
    "phenotype_onset_with_FastHPOCR_pipeline_outputs"
)
PHENOTYPE_ONSET_WITHOUT_FASTHPOCR_OUTPUTS_DIR = (
    "phenotype_onset_without_FastHPOCR_pipeline_outputs"
)


def get_args() -> dict:
    parser = argparse.ArgumentParser(
        description="Noonan Syndrome Extraction Patterns Pipeline."
    )
    parser.add_argument(
        "pipeline",
        default=None,
        choices=["1", "2", "3", "4"],
        help="Choose which pipeline to run.",
    )
    parser.add_argument("--run-all", action="store_true", help="Run all 4 pipelines.")
    args = parser.parse_args()
    args_dict: dict[str, str] = {
        "pipeline": args.pipeline,
        "run_all": args.run_all,
    }
    return args_dict


def preprocess(url):
    noonan_gene_reviews = HTMLProcessor(url=url, path=None)
    partitions = noonan_gene_reviews.split_html("h2", avoid_tags=["h2", "h3", "h4"])
    print(f"Preprocessing step complete! {len(partitions)} partitions generated.")

    small_test = partitions[:10]
    return small_test
    # return partitions


from annotate import annotate_text


# Phenotype candidates extraction
def extract_phenotypes(text_partitions: list):
    text_phenotype_pair = []
    phenotype_candidates = []

    for text in tqdm(text_partitions):
        hpo_result = annotate_text(HPO_INDEX_DIR, text, print_result=False)

        if hpo_result:
            text = text.replace('"', '\\"')
            text_phenotype_pair.append((text, hpo_result))
            hpo_result_split = [part.strip() for part in hpo_result.split(";")]
            for split in hpo_result_split:
                phenotype_candidates.append(split)
        else:
            print(f"No HPO result for text: \n{text}")
    return text_phenotype_pair, phenotype_candidates


import json


def generate_extraction_prompt(prompt_template, phenotype_candidates, output_file):
    with open(prompt_template, "r") as prompt_file:
        template = prompt_file.read()

    prompt_list = []

    for text, hpo_result in phenotype_candidates:
        modified_prompt_str = template
        modified_prompt_str = modified_prompt_str.replace("{{hpo_terms}}", hpo_result)
        modified_prompt_str = modified_prompt_str.replace("{{clinical_text}}", text)

        try:
            modified_prompt = json.loads(modified_prompt_str, strict=False)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print(f"Problematic JSON string: {modified_prompt_str}")

        prompt_list.append(modified_prompt)

    print(f"{len(prompt_list)} prompts generated.")
    output_str = json.dumps(prompt_list, indent=4)

    with open(output_file, "w") as out_file:
        out_file.write(output_str)

    return prompt_list


import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import time


def run_model(prompts):
    torch.random.manual_seed(0)
    model = AutoModelForCausalLM.from_pretrained(
        "microsoft/Phi-3-mini-128k-instruct",
        device_map="cuda",
        torch_dtype="auto",
        trust_remote_code=True,
    )
    tokenizer = AutoTokenizer.from_pretrained("microsoft/Phi-3-mini-128k-instruct")
    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
    )
    generation_args = {
        "max_new_tokens": 256,
        "return_full_text": False,
        "temperature": 0.0,
        "do_sample": False,
    }
    output_str = ""
    model_output = []
    start = time.time()

    for prompt in tqdm(prompts):
        output = pipe(prompt, **generation_args)
        output_str += output[0]["generated_text"].strip()
        out_str = output[0]["generated_text"].strip()
        # print("\nOUTPUT GENERATED:")
        # print(out_str)
        output_str += "\n"
        model_output.append(out_str)

    end = time.time()
    length = end - start
    print(f"LLM task complete at {length:.2f} secs.")
    return model_output


import re


# Post-process: remove N/A outputs
def remove_NA_outputs(model_output):
    output_data = model_output
    phenotype_concept_pairs = []

    for output in output_data:
        # Remove any multiple newlines
        output = re.sub(r"\n+", "\n", output).strip()
        output_splits = output.split("\n")

        for line in output_splits:
            # Split concepts separated by "|"
            line_splits = line.split("|")
            if len(line_splits) == 2:
                concept_value = line_splits[1].strip()

                if concept_value != "N/A":
                    phenotype_concept_pairs.append(line)
            elif len(line_splits) == 1:
                # If this is just a newline after concept pair, skip it
                if line_splits[0] == "":
                    pass
                else:
                    phenotype_concept_pairs.append(line)
            else:
                phenotype_concept_pairs.append(line)
    return phenotype_concept_pairs


# Specifically for phenotype candidates created by LLM
def remove_NA_candidates(phenotype_candidate_and_text_pairs):
    phenotype_and_text_pair = []
    phenotype_candidates = []
    for phenotype_candidate, text in phenotype_candidate_and_text_pairs:
        candidate = phenotype_candidate.strip()
        if candidate != "N/A":
            phenotype_and_text_pair.append((phenotype_candidate, text))

            candidate_split = [part.strip() for part in candidate.split(";")]
            for split in candidate_split:
                phenotype_candidates.append(split)
    return phenotype_and_text_pair, phenotype_candidates


def clean_model_outputs(model_output):
    phenotypes = []
    concepts = []
    valid_outputs = []
    for output in model_output:
        if output != "":
            split_result = output.split("\n")
            for concept_pair in split_result:
                concept_pair_split = concept_pair.split("|")

                if len(concept_pair_split) == 2:
                    phenotype_value = concept_pair_split[0].strip()
                    concept_value = concept_pair_split[1].strip()
                    phenotypes.append(phenotype_value)
                    concepts.append(concept_value)
                    valid_outputs.append(concept_pair)
    return valid_outputs, phenotypes, concepts


def validate_phenotypes(phenotype_concept_pairs):
    new_pairs_tuple = []
    valid_phenotype = []
    concepts = []
    for phenotype, concept in tqdm(phenotype_concept_pairs):
        hpo_result = annotate_text(HPO_INDEX_DIR, phenotype, print_result=False)
        if hpo_result:
            new_pairs_tuple.append((phenotype, concept))
            valid_phenotype.append(phenotype)
            concepts.append(concept)
        else:
            print(f"No HPO result for: \n{phenotype}")
    return new_pairs_tuple, valid_phenotype, concepts


def generate_concept_validation_prompt(
    prompt_template, concept_candidates, output_file
):
    with open(prompt_template, "r") as prompt_file:
        template = prompt_file.read()

    val_prompt_list = []

    for text in concept_candidates:
        modified_prompt_str = template
        modified_prompt_str = modified_prompt_str.replace("{{text}}", text.lower())

        try:
            modified_prompt = json.loads(modified_prompt_str, strict=False)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print(f"Problematic JSON string: {modified_prompt_str}")

        val_prompt_list.append(modified_prompt)

    print(f"{len(val_prompt_list)} prompts generated.")
    output_str = json.dumps(val_prompt_list, indent=4)

    with open(output_file, "w") as out_file:
        out_file.write(output_str)

    return val_prompt_list


def generate_phenotype_extraction_prompt(prompt_template, text_partitions, output_file):
    with open(prompt_template, "r") as prompt_file:
        template = prompt_file.read()

    prompt_list = []
    for text in text_partitions:
        modified_prompt_str = template
        modified_prompt_str = modified_prompt_str.replace("{{text}}", text)

        try:
            modified_prompt = json.loads(modified_prompt_str, strict=False)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print(f"Problematic JSON string: {modified_prompt_str}")

        prompt_list.append(modified_prompt)

    print(f"{len(prompt_list)} prompts generated.")
    output_str = json.dumps(prompt_list, indent=4)

    with open(output_file, "w") as out_file:
        out_file.write(output_str)
    return prompt_list


def filter_boolean(text):
    # Check for the presence of both "TRUE" and "FALSE"
    contains_true = bool(re.search(r"\bTRUE\b", text))
    contains_false = bool(re.search(r"\bFALSE\b", text))

    # If both "TRUE" and "FALSE" are present, return "NULL"
    if contains_true and contains_false:
        return "NULL"

    matches = re.findall(r"TRUE", text.strip())
    if len(matches) >= 1:
        return "TRUE"

    matches = re.findall(r"FALSE", text.strip())
    if len(matches) >= 1:
        return "FALSE"

    return ""


# REMOVE ANY ACCESS STUFF THAT COMES AFTER "TRUE" OR "FALSE"
def clean_validation_outputs(output_list):
    concept_validation = []
    for output in output_list:
        concept_bool = filter_boolean(output)
        concept_validation.append(concept_bool)
    return concept_validation


def process_concept_validation(concept_validation_tuples):
    new_pairs_tuple = []
    phenotypes = []
    valid_concepts = []
    for phenotype, concept, bool in concept_validation_tuples:
        if bool == "TRUE":
            new_pairs_tuple.append((phenotype, concept))
            phenotypes.append(phenotype)
            valid_concepts.append(concept)
    return new_pairs_tuple, phenotypes, valid_concepts


def serialise_tuple_pair(data_to_serialise: list, output_file_path: str):
    output_str = ""
    start_line = True
    for tuple_one, tuple_two in data_to_serialise:
        if not start_line:
            output_str += f"\n{tuple_one}, {tuple_two}"
        else:
            output_str += f"{tuple_one}, {tuple_two}"
            start_line = False

    with open(output_file_path, "w") as output_file:
        output_file.write(output_str)


def serialise_single_list(data_to_serialise: list, output_csv_path: str):
    output_str = ""
    start_line = True
    for data in data_to_serialise:
        if not start_line:
            output_str += f",\n{data}"
        else:
            output_str += f"{data}"
            start_line = False

    with open(output_csv_path, "w") as output_file:
        output_file.write(output_str)


def serialise_validation_list(data_to_serialise: list, output_file_path: str):
    output_str = ""
    start_line = True
    for tuple_one, tuple_two, tuple_three in data_to_serialise:
        if not start_line:
            output_str += f"\n{tuple_one} | {tuple_two} | {tuple_three}"
        else:
            output_str += f"{tuple_one} | {tuple_two} | {tuple_three}"
            start_line = False

    with open(output_file_path, "w") as output_file:
        output_file.write(output_str)


def serialise_concept_pairs(data_to_serialise: list, output_file_path: str):
    output_str = ""
    start_line = True
    for tuple_one, tuple_two in data_to_serialise:
        if not start_line:
            output_str += f"\n{tuple_one} | {tuple_two}"
        else:
            output_str += f"{tuple_one} | {tuple_two}"
            start_line = False

    with open(output_file_path, "w") as output_file:
        output_file.write(output_str)


# Phenotype-frequency extraction with FastHPOCR
def pipeline_one():
    print("Running PIPELINE 1 - Phenotype-frequency extraction with FastHPOCR...")
    reset_directory(PHENOTYPE_FREQUENCY_WITH_FASTHPOCR_OUTPUTS_DIR)

    PHENOTYPE_CANDIDATES = path.join(
        PHENOTYPE_FREQUENCY_WITH_FASTHPOCR_OUTPUTS_DIR,
        "FastHPOCR_phenotype_candidates.csv",
    )
    PHENOTYPE_FREQUENCY_EXTRACTION_PROMPTS = path.join(
        PHENOTYPE_FREQUENCY_WITH_FASTHPOCR_OUTPUTS_DIR,
        "phenotype_frequency_extraction_prompts.json",
    )
    PHENOTYPE_FREQUENCY_MODEL_OUTPUT = path.join(
        PHENOTYPE_FREQUENCY_WITH_FASTHPOCR_OUTPUTS_DIR,
        "phenotype_frequency_model_output.txt",
    )
    PHENOTYPE_FREQUENCY_VALIDATION_PROMPTS = path.join(
        PHENOTYPE_FREQUENCY_WITH_FASTHPOCR_OUTPUTS_DIR,
        "phenotype_frequency_validation_prompts.json",
    )
    FREQUENCY_VALIDATION = path.join(
        PHENOTYPE_FREQUENCY_WITH_FASTHPOCR_OUTPUTS_DIR, "frequency_validation.txt"
    )
    PHENOTYPE_FREQUENCY_WITH_FASTHPOCR_RESULTS = path.join(
        PHENOTYPE_FREQUENCY_WITH_FASTHPOCR_OUTPUTS_DIR, "pipeline_results.txt"
    )

    # STEP 1: Split HMTL into partitions
    html_partitions = preprocess(URL)

    # STEP 2: Extract phenotype candidates with FastHPOCR
    text_phenotype_candidate_pair, phenotype_candidates = extract_phenotypes(
        html_partitions
    )
    serialise_single_list(phenotype_candidates, PHENOTYPE_CANDIDATES)

    # STEP 3: Generate prompts in preparation for the phenotype-frequency extraction task
    phenotype_frequency_extraction_prompts = generate_extraction_prompt(
        PHENOTYPE_FREQUENCY_EXTRACTION_PROMPT_TEMPLATE,
        text_phenotype_candidate_pair,
        PHENOTYPE_FREQUENCY_EXTRACTION_PROMPTS,
    )

    # STEP 4: Perform phenotype-frequency extraction task
    phenotype_frequency_outputs = run_model(phenotype_frequency_extraction_prompts)
    serialise_single_list(phenotype_frequency_outputs, PHENOTYPE_FREQUENCY_MODEL_OUTPUT)

    # STEP 5: Remove phenotype-frequency pairs with 'N/A' frequency value
    phenotype_frequency_outputs = remove_NA_outputs(phenotype_frequency_outputs)

    # STEP 6: Clean model output by removing pairs with invalid formats
    _, phenotypes, frequencies = clean_model_outputs(phenotype_frequency_outputs)

    # STEP 7: Validate phenotypes with FastHPOCR
    phenotype_frequency_pairs = list(zip(phenotypes, frequencies))
    phenotype_frequency_pairs, valid_phenotypes, frequencies = validate_phenotypes(
        phenotype_frequency_pairs
    )

    # STEP 8: Generate prompts in preparation for the frequency validation task
    frequency_validation_prompts = generate_concept_validation_prompt(
        FREQUENCY_VALIDATION_PROMPT_TEMPLATE,
        frequencies,
        PHENOTYPE_FREQUENCY_VALIDATION_PROMPTS,
    )

    # STEP 9: Perform frequency validation task with LLM
    frequency_validation_outputs = run_model(frequency_validation_prompts)

    # STEP 10: Clean boolean outputs from frequency validation task (remove all 'FALSE' frequency values)
    frequency_validation = clean_validation_outputs(frequency_validation_outputs)
    frequency_validation_tuples = list(
        zip(valid_phenotypes, frequencies, frequency_validation)
    )
    serialise_validation_list(frequency_validation_tuples, FREQUENCY_VALIDATION)

    # STEP 11: Process valid frequencies and generate a new list with only valid phenotype-frequency pair
    final_pairs, _, _ = process_concept_validation(frequency_validation_tuples)
    serialise_concept_pairs(final_pairs, PHENOTYPE_FREQUENCY_WITH_FASTHPOCR_RESULTS)

    print("PIPELINE 1 - Phenotype-frequency extraction with FastHPOCR completed successfully!")
    print(
        f"Pipeline outputs has been saved in the directory: '{PHENOTYPE_FREQUENCY_WITH_FASTHPOCR_OUTPUTS_DIR}'"
    )


# Phenotype-frequency extraction without FastHPOCR
def pipeline_two():
    print("Running PIPELINE 2 - Phenotype-frequency extraction without FastHPOCR...")
    reset_directory(PHENOTYPE_FREQUENCY_WITHOUT_FASTHPOCR_OUTPUTS_DIR)

    PHENOTYPE_EXTRACTION_PROMPTS = path.join(
        PHENOTYPE_FREQUENCY_WITHOUT_FASTHPOCR_OUTPUTS_DIR,
        "phenotype_extraction_prompts.json",
    )
    MODEL_PHENOTYPE_CANDIDATES = path.join(
        PHENOTYPE_FREQUENCY_WITHOUT_FASTHPOCR_OUTPUTS_DIR,
        "model_phenotype_candidates.csv",
    )
    PHENOTYPE_FREQUENCY_EXTRACTION_PROMPTS = path.join(
        PHENOTYPE_FREQUENCY_WITHOUT_FASTHPOCR_OUTPUTS_DIR,
        "phenotype_frequency_extraction_prompts.json",
    )
    FREQUENCY_VALIDATION_PROMPTS = path.join(
        PHENOTYPE_FREQUENCY_WITHOUT_FASTHPOCR_OUTPUTS_DIR,
        "frequency_validation_prompts.json",
    )
    FREQUENCY_VALIDATION = path.join(
        PHENOTYPE_FREQUENCY_WITHOUT_FASTHPOCR_OUTPUTS_DIR, "frequency_validation.txt"
    )
    PHENOTYPE_FREQUENCY_WITHOUT_FASTHPOCR_RESULTS = path.join(
        PHENOTYPE_FREQUENCY_WITHOUT_FASTHPOCR_OUTPUTS_DIR, "pipeline_results.txt"
    )

    # STEP 1: Split HMTL into partitions
    html_partitions = preprocess(URL)

    # STEP 2: Generate prompt to extract phenotype candidates
    phenotype_extraction_prompts = generate_phenotype_extraction_prompt(
        PHENOTYPE_EXTRACTION_TEMPLATE, html_partitions, PHENOTYPE_EXTRACTION_PROMPTS
    )

    # STEP 3: Extract phenotype candidates with LLM
    phenotype_candidate_outputs = run_model(phenotype_extraction_prompts)

    # STEP 4: Remove phenotype candidates that are 'N/A'
    phenotype_text_partition_pairs = list(
        zip(phenotype_candidate_outputs, html_partitions)
    )
    phenotype_text_partition_pairs, phenotype_candidates = remove_NA_candidates(
        phenotype_text_partition_pairs
    )

    serialise_single_list(phenotype_candidates, MODEL_PHENOTYPE_CANDIDATES)

    # STEP 5: Generate prompts in preparation for the phenotype-frequency extraction task
    phenotype_frequency_extraction_prompts = generate_extraction_prompt(
        PHENOTYPE_FREQUENCY_EXTRACTION_PROMPT_TEMPLATE,
        phenotype_text_partition_pairs,
        PHENOTYPE_FREQUENCY_EXTRACTION_PROMPTS,
    )

    # STEP 6: Perform phenotype-frequency extraction task
    phenotype_frequency_outputs = run_model(phenotype_frequency_extraction_prompts)

    # STEP 7: Remove phenotype-frequency pairs with 'N/A' frequency value
    phenotype_frequency_outputs = remove_NA_outputs(phenotype_frequency_outputs)

    # STEP 8: Clean model output by removing pairs with invalid formats
    _, phenotypes, frequencies = clean_model_outputs(phenotype_frequency_outputs)

    # STEP 9: Validate phenotypes with FastHPOCR
    phenotype_frequency_pairs = list(zip(phenotypes, frequencies))
    phenotype_frequency_pairs, valid_phenotypes, frequencies = validate_phenotypes(
        phenotype_frequency_pairs
    )

    # STEP 10: Generate prompts in preparation for the frequency validation task
    frequency_validation_prompts = generate_concept_validation_prompt(
        FREQUENCY_VALIDATION_PROMPT_TEMPLATE,
        frequencies,
        FREQUENCY_VALIDATION_PROMPTS,
    )

    # STEP 11: Perform frequency validation task with LLM
    frequency_validation_outputs = run_model(frequency_validation_prompts)

    # STEP 12: Clean boolean outputs from frequency validation task (remove all 'FALSE' frequency values)
    frequency_validation = clean_validation_outputs(frequency_validation_outputs)
    frequency_validation_tuples = list(
        zip(valid_phenotypes, frequencies, frequency_validation)
    )
    serialise_validation_list(frequency_validation_tuples, FREQUENCY_VALIDATION)

    # STEP 13: Process valid frequencies and generate a new list with only valid phenotype-frequency pair
    final_pairs, _, _ = process_concept_validation(frequency_validation_tuples)
    serialise_concept_pairs(final_pairs, PHENOTYPE_FREQUENCY_WITHOUT_FASTHPOCR_RESULTS)

    print("PIPELINE 2 - Phenotype-frequency extraction without FastHPOCR completed successfully!")
    print(
        f"Pipeline outputs has been saved in the directory: '{PHENOTYPE_FREQUENCY_WITHOUT_FASTHPOCR_OUTPUTS_DIR}'"
    )


# Phenotype-onset extraction with FastHPOCR
def pipeline_three():
    print("Running PIPELINE 3 - Phenotype-onset extraction with FastHPOCR...")
    reset_directory(PHENOTYPE_ONSET_WITH_FASTHPOCR_OUTPUTS_DIR)

    PHENOTYPE_CANDIDATES = path.join(
        PHENOTYPE_ONSET_WITH_FASTHPOCR_OUTPUTS_DIR, "FastHPOCR_phenotype_candidates.csv"
    )
    PHENOTYPE_ONSET_MODEL_OUTPUT = path.join(
        PHENOTYPE_ONSET_WITH_FASTHPOCR_OUTPUTS_DIR, "phenotype_onset_model_output.txt"
    )
    PHENOTYPE_ONSET_EXTRACTION_PROMPTS = path.join(
        PHENOTYPE_ONSET_WITH_FASTHPOCR_OUTPUTS_DIR,
        "phenotype_onset_extraction_prompts.json",
    )
    PHENOTYPE_ONSET_VALIDATION_PROMPTS = path.join(
        PHENOTYPE_ONSET_WITH_FASTHPOCR_OUTPUTS_DIR,
        "phenotype_onset_validation_prompts.json",
    )
    ONSET_VALIDATION = path.join(
        PHENOTYPE_ONSET_WITH_FASTHPOCR_OUTPUTS_DIR, "onset_validation.txt"
    )
    PHENOTYPE_ONSET_WITH_FASTHPOCR_RESULTS = path.join(
        PHENOTYPE_ONSET_WITH_FASTHPOCR_OUTPUTS_DIR, "pipeline_results.txt"
    )

    # STEP 1: Split HMTL into partitions
    html_partitions = preprocess(URL)

    # STEP 2: Extract phenotype candidates with FastHPOCR
    text_phenotype_candidate_pair, phenotype_candidates = extract_phenotypes(
        html_partitions
    )
    serialise_single_list(phenotype_candidates, PHENOTYPE_CANDIDATES)

    # STEP 3: Generate prompts in preparation for the phenotype-onset extraction task
    phenotype_onset_extraction_prompts = generate_extraction_prompt(
        PHENOTYPE_ONSET_EXTRACTION_PROMPT_TEMPLATE,
        text_phenotype_candidate_pair,
        PHENOTYPE_ONSET_EXTRACTION_PROMPTS,
    )

    # STEP 4: Perform phenotype-onset extraction task
    phenotype_onset_outputs = run_model(phenotype_onset_extraction_prompts)
    serialise_single_list(phenotype_onset_outputs, PHENOTYPE_ONSET_MODEL_OUTPUT)

    # STEP 5: Remove phenotype-onsets pairs with 'N/A' onset value
    phenotype_onset_outputs = remove_NA_outputs(phenotype_onset_outputs)

    # STEP 6: Clean model output by removing pairs with invalid formats
    _, phenotypes, onsets = clean_model_outputs(phenotype_onset_outputs)

    # STEP 7: Validate phenotypes with FastHPOCR
    phenotype_onset_pairs = list(zip(phenotypes, onsets))
    phenotype_onset_pairs, valid_phenotypes, onsets = validate_phenotypes(
        phenotype_onset_pairs
    )

    # STEP 8: Generate prompts in preparation for the onset validation task
    onset_validation_prompts = generate_concept_validation_prompt(
        ONSET_VALIDATION_PROMPT_TEMPLATE,
        onsets,
        PHENOTYPE_ONSET_VALIDATION_PROMPTS,
    )

    # STEP 9: Perform onset validation task with LLM
    onset_validation_outputs = run_model(onset_validation_prompts)

    # STEP 10: Clean boolean outputs from onset validation task (remove all 'FALSE' onset values)
    onset_validation = clean_validation_outputs(onset_validation_outputs)
    onset_validation_tuples = list(zip(valid_phenotypes, onsets, onset_validation))
    serialise_validation_list(onset_validation_tuples, ONSET_VALIDATION)

    # STEP 11: Process valid onsets and generate a new list with only valid phenotype-onsets pair
    final_pairs, _, _ = process_concept_validation(onset_validation_tuples)
    serialise_concept_pairs(final_pairs, PHENOTYPE_ONSET_WITH_FASTHPOCR_RESULTS)

    print("PIPELINE 3 - Phenotype-onset extraction with FastHPOCR completed successfully!")
    print(
        f"Pipeline outputs has been saved in the directory: '{PHENOTYPE_ONSET_WITH_FASTHPOCR_OUTPUTS_DIR}'"
    )


# Phenotype-onset extraction without FastHPOCR
def pipeline_four():
    print("Running PIPELINE 4 - Phenotype-onset extraction without FastHPOCR...")
    reset_directory(PHENOTYPE_ONSET_WITHOUT_FASTHPOCR_OUTPUTS_DIR)

    PHENOTYPE_EXTRACTION_PROMPTS = path.join(
        PHENOTYPE_ONSET_WITHOUT_FASTHPOCR_OUTPUTS_DIR,
        "phenotype_extraction_prompts.json",
    )
    MODEL_PHENOTYPE_CANDIDATES = path.join(
        PHENOTYPE_ONSET_WITHOUT_FASTHPOCR_OUTPUTS_DIR, "model_phenotype_candidates.csv"
    )
    PHENOTYPE_ONSET_EXTRACTION_PROMPTS = path.join(
        PHENOTYPE_ONSET_WITHOUT_FASTHPOCR_OUTPUTS_DIR,
        "phenotype_onset_extraction_prompts.json",
    )
    ONSET_VALIDATION_PROMPTS = path.join(
        PHENOTYPE_ONSET_WITHOUT_FASTHPOCR_OUTPUTS_DIR, "onset_validation_prompts.json"
    )
    ONSET_VALIDATION = path.join(
        PHENOTYPE_ONSET_WITHOUT_FASTHPOCR_OUTPUTS_DIR, "onset_validation.txt"
    )
    PHENOTYPE_ONSET_WITHOUT_FASTHPOCR_RESULTS = path.join(
        PHENOTYPE_ONSET_WITHOUT_FASTHPOCR_OUTPUTS_DIR, "pipeline_results.txt"
    )
    # STEP 1: Split HMTL into partitions
    html_partitions = preprocess(URL)

    # STEP 2: Generate prompt to extract phenotype candidates
    phenotype_extraction_prompts = generate_phenotype_extraction_prompt(
        PHENOTYPE_EXTRACTION_TEMPLATE, html_partitions, PHENOTYPE_EXTRACTION_PROMPTS
    )

    # STEP 3: Extract phenotype candidates with LLM
    phenotype_candidate_outputs = run_model(phenotype_extraction_prompts)

    # STEP 4: Remove phenotype candidates that are 'N/A'
    phenotype_text_partition_pairs = list(
        zip(phenotype_candidate_outputs, html_partitions)
    )
    phenotype_text_partition_pairs, phenotype_candidates = remove_NA_candidates(
        phenotype_text_partition_pairs
    )

    serialise_single_list(phenotype_candidates, MODEL_PHENOTYPE_CANDIDATES)

    # STEP 5: Generate prompts in preparation for the phenotype-onsets extraction task
    phenotype_onset_extraction_prompts = generate_extraction_prompt(
        PHENOTYPE_ONSET_EXTRACTION_PROMPT_TEMPLATE,
        phenotype_text_partition_pairs,
        PHENOTYPE_ONSET_EXTRACTION_PROMPTS,
    )

    # STEP 6: Perform phenotype-onset extraction task
    phenotype_onset_outputs = run_model(phenotype_onset_extraction_prompts)

    # STEP 7: Remove phenotype-onset pairs with 'N/A' onset value
    phenotype_onset_outputs = remove_NA_outputs(phenotype_onset_outputs)

    # STEP 8: Clean model output by removing pairs with invalid formats
    _, phenotypes, onsets = clean_model_outputs(phenotype_onset_outputs)

    # STEP 9: Validate phenotypes with FastHPOCR
    phenotype_onset_pairs = list(zip(phenotypes, onsets))
    phenotype_onset_pairs, valid_phenotypes, onsets = validate_phenotypes(
        phenotype_onset_pairs
    )

    # STEP 10: Generate prompts in preparation for the onset validation task
    onset_validation_prompts = generate_concept_validation_prompt(
        ONSET_VALIDATION_PROMPT_TEMPLATE,
        onsets,
        ONSET_VALIDATION_PROMPTS,
    )

    # STEP 11: Perform onset validation task with LLM
    onset_validation_outputs = run_model(onset_validation_prompts)

    # STEP 12: Clean boolean outputs from onset validation task (remove all 'FALSE' onset values)
    onset_validation = clean_validation_outputs(onset_validation_outputs)
    onset_validation_tuples = list(zip(valid_phenotypes, onsets, onset_validation))
    serialise_validation_list(onset_validation_tuples, ONSET_VALIDATION)

    # STEP 13: Process valid onset and generate a new list with only valid phenotype-onset pair
    final_pairs, _, _ = process_concept_validation(onset_validation_tuples)
    serialise_concept_pairs(final_pairs, PHENOTYPE_ONSET_WITHOUT_FASTHPOCR_RESULTS)

    print("PIPELINE 4 - Phenotype-onset extraction without FastHPOCR completed successfully!")
    print(
        f"Pipeline outputs has been saved in the directory: '{PHENOTYPE_ONSET_WITHOUT_FASTHPOCR_OUTPUTS_DIR}'"
    )


import shutil
import os


def reset_directory(path_dir: str):
    if os.path.exists(path_dir):
        try:
            shutil.rmtree(path_dir)
            print(f"Removed directory and its contents: {path_dir}")
        except Exception as e:
            print(f"Error removing directory: {e}")
    else:
        print(f"Directory does not exist: {path_dir}")
        print("Skipping.")

    try:
        os.makedirs(path_dir)
        print(f"Recreated directory: {path_dir}")
    except Exception as e:
        print(f"Error creating directory: {e}")


def main():
    args: dict = get_args()
    pipeline = args.get("pipeline")
    run_all = args.get("run_all")

    if run_all:
        print("Running all 4 pipelines...")
        pipeline_one()
        pipeline_two()
        pipeline_three()
        pipeline_four()
    elif pipeline == "1":
        pipeline_one()
    elif pipeline == "2":
        pipeline_two()
    elif pipeline == "3":
        pipeline_three()
    elif pipeline == "4":
        pipeline_four()
    else:
        print("ERROR!")


if __name__ == "__main__":
    main()
