import pandas as pd

def process_concept_pairs(file):
    with open(file, "r") as results_file:
        results = results_file.read().lower()

    rows = results.strip().split("\n")
    concept_pairs = []

    for line in rows:
        line_split = line.split("|")
        phenotype_concept = line_split[0]
        concept = line_split[1]
        concept_pairs.append((phenotype_concept.strip(), concept.strip()))
    return concept_pairs


def process_phenotype_onset_pairs(file):
    with open(file, "r") as results_file:
        results = results_file.read().lower()
    
    rows = results.strip().split("\n")
    phenotype_onset_pairs = []

    for line in rows:
        line_split = line.split("|")
        phenotype = line_split[0]
        onset_group = line_split[1]
        onset_split = onset_group.split(";")
        for onset in onset_split:
            phenotype_onset_pairs.append((phenotype.strip(), onset.strip()))
    return phenotype_onset_pairs


def calculate_precision(gold_standard, model_output, concept):
    gold_standard_df = pd.DataFrame(gold_standard, columns=["phenotype", concept])
    model_output_df = pd.DataFrame(model_output, columns=["phenotype", concept]) 

    matching_pairs = pd.merge(gold_standard_df, model_output_df, on=["phenotype", concept], how="inner")
    total_matching_pairs = len(matching_pairs)

    # Get all pairs and find non-matching pairs
    all_pairs = pd.merge(gold_standard_df, model_output_df, on=["phenotype", concept], how="outer", indicator=True)

    # Filter for non-matching pairs from model outputs only
    non_matching_pairs_from_model_output = all_pairs[all_pairs['_merge'] == 'right_only']
    total_non_matching_pairs = len(non_matching_pairs_from_model_output)

    # Precision evaluation
    print(f"True Positives (TP): {total_matching_pairs} pairs") # Number of matching pairs (correct pairs extraced)
    print(f"False Positives (FP): {total_non_matching_pairs} pairs") # Number of non matching pairs (incorrect pairs extracted)

    tp = total_matching_pairs
    fp = total_non_matching_pairs
    precision = tp / (tp + fp)
    rounded_precision = round(precision, 2)

    print(f"Precision: {rounded_precision}")


# Gold standard directories
PHENOTYPE_FREQUENCY_GOLD_STANDARD = "gold_standard/phenotype_frequency_gold_standard.txt"
PHENOTYPE_ONSET_GOLD_STANDARD = "gold_standard/phenotype_onset_gold_standard.txt"

# Pipeline output paths
PHENOTYPE_FREQUENCY_WITH_FASTHPOCR = "phenotype_frequency_with_FastHPOCR_pipeline_outputs/pipeline_results.txt"
PHENOTYPE_FREQUENCY_WITHOUT_FASTHPOCR = "phenotype_frequency_without_FastHPOCR_pipeline_outputs/pipeline_results.txt"
PHENOTYPE_ONSET_WITH_FASTHPOCR = "phenotype_onset_with_FastHPOCR_pipeline_outputs/pipeline_results.txt"
PHENOTYPE_ONSET_WITHOUT_FASTHPOCR = "phenotype_onset_without_FastHPOCR_pipeline_outputs/pipeline_results.txt"

def main():
    # Process gold standard
    phenotype_frequency_gold_standard = process_concept_pairs(PHENOTYPE_FREQUENCY_GOLD_STANDARD)
    phenotype_onset_gold_standard = process_concept_pairs(PHENOTYPE_ONSET_GOLD_STANDARD)

    # Pipeline 1 - Phenotype-frequency with FastHPOCR
    print("Phenotype-frequency with FastHPOCR evauluation...")
    phenotype_frequency_with_FastHPOCR = process_concept_pairs(PHENOTYPE_FREQUENCY_WITH_FASTHPOCR)
    calculate_precision(phenotype_frequency_gold_standard, phenotype_frequency_with_FastHPOCR, "frequency")

    # Pipeline 2 - Phenotype-frequency without FastHPOCR
    print("Phenotype-frequency without FastHPOCR evauluation...")
    phenotype_frequency_without_FastHPOCR = process_concept_pairs(PHENOTYPE_FREQUENCY_WITHOUT_FASTHPOCR)
    calculate_precision(phenotype_frequency_gold_standard, phenotype_frequency_without_FastHPOCR, "frequency")

    # Pipeline 3 - Phenotype-onset with FastHPOCR
    print("Phenotype-onset with FastHPOCR evauluation...")
    phenotype_onset_with_FastHPOCR = process_phenotype_onset_pairs(PHENOTYPE_ONSET_WITH_FASTHPOCR)
    calculate_precision(phenotype_onset_gold_standard, phenotype_onset_with_FastHPOCR, "onset")

    # Pipeline 4 - Phenotype-onset without FastHPOCR
    print("Phenotype-onset without FastHPOCR evauluation...")
    phenotype_onset_without_FastHPOCR = process_phenotype_onset_pairs(PHENOTYPE_ONSET_WITHOUT_FASTHPOCR)
    calculate_precision(phenotype_onset_gold_standard, phenotype_onset_without_FastHPOCR, "onset")

if __name__ == "__main__":
    main()