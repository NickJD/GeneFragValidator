import gzip
import matplotlib.pyplot as plt
from collections import defaultdict

# Step 1: Parse BLAST output file to identify predictions with hits
predictions_with_hit = set()
with open('../Genome_Processing/Mycoplasma_genitalium_G37/FragGeneScan/FragGeneScan_ART_errFree_Combined_DP_80', 'r') as blast_file:
    for line in blast_file:
        fields = line.strip().split('\t')
        predictions_with_hit.add(fields[0].replace('@', ''))  # Assuming the first column contains prediction IDs

# Step 2: Compare predictions with hits to all predictions to identify those without hits
predictions_all = defaultdict(str)
with open('../Genome_Processing/Mycoplasma_genitalium_G37/FragGeneScan/FragGeneScan_ART_errFree_Combined.faa', 'r') as predictions_file:
    sequence = ''
    for line in predictions_file:
        if line.startswith('>'):
            if sequence:  # If there's a sequence accumulated, add it to the dictionary
                predictions_all[prediction_id] = sequence
                sequence = ''  # Reset sequence
            prediction_id = line.strip().replace('>', '').replace('@', '')
        else:
            sequence += line.strip()  # Accumulate the sequence

    # Add the last sequence since there's no new header after it
    if sequence:
        predictions_all[prediction_id] = sequence

# Step 3: Extract IDs of predictions without hits
predictions_without_hit = {prediction_id: sequence for prediction_id, sequence in predictions_all.items() if
                           prediction_id not in predictions_with_hit}

# Step 4: Search for IDs in Eggnog mapper output file and extract COG category for unmapped reads
cog_categories = defaultdict(int)
with open(
        '../Genome_Processing/Mycoplasma_genitalium_G37/FragGeneScan/FragGeneScan_ART_errFree_Combined_Emapper.emapper.annotations',
        'rt') as eggnog_file:
    for line in eggnog_file:
        if line.startswith('#'):
            continue
        fields = line.strip().split('\t')
        prediction_id = fields[0][1:]  # Remove '@' from the beginning
        if prediction_id in predictions_without_hit:
            cogs = fields[6]  # Assuming COG category is in the 7th column
            for cog in cogs:
                if cog != 'Z' and cog != '-':
                    cog_categories[cog] += 1

# Step 5: Calculate the proportion of each COG category for unmapped reads
total_unmapped_predictions = len(predictions_without_hit)
print("Number of Unmapped Predictions: " + str(total_unmapped_predictions))
unmapped_proportions = {cog: count / total_unmapped_predictions * 100 for cog, count in cog_categories.items()}

# Step 6: Report the proportion of each COG category for unmapped reads
for cog, proportion in unmapped_proportions.items():
    print(f"COG category {cog}: {proportion:.2f}%")

# Step 7: Collect COG assignments for mapped reads
mapped_cog_categories = defaultdict(int)
with open(
        '../Genome_Processing/Mycoplasma_genitalium_G37/FragGeneScan/FragGeneScan_ART_errFree_Combined_Emapper.emapper.annotations',
        'rt') as eggnog_file:
    for line in eggnog_file:
        if line.startswith('#'):
            continue
        fields = line.strip().split('\t')
        prediction_id = fields[0][1:]  # Remove '@' from the beginning
        if prediction_id in predictions_with_hit:
            cogs = fields[6]  # Assuming COG category is in the 7th column
            for cog in cogs:
                if cog != 'Z' and cog != '-':
                    mapped_cog_categories[cog] += 1

# Step 8: Calculate the proportion of each COG category for mapped reads
total_mapped_predictions = len(predictions_with_hit)
mapped_proportions = {cog: count / total_mapped_predictions * 100 for cog, count in mapped_cog_categories.items()}

# Sort COGs
sorted_cogs = sorted(cog_categories.keys())

# Calculate differences between unmapped and mapped proportions
diffs = [unmapped_proportions[cog] - mapped_proportions[cog] for cog in sorted_cogs]

# Plot differences
plt.figure(figsize=(12, 8))
plt.plot(sorted_cogs, diffs, label='Unmapped - Mapped', linestyle='-')
plt.xlabel('COG Category', fontsize=24)
plt.ylabel('Difference (Unmapped - Mapped)', fontsize=24)
plt.title('Differences between Unmapped and Mapped COG Proportions', fontsize=24)
plt.xticks(rotation=45, ha='right', fontsize=14)
plt.yticks(fontsize=14)
plt.legend(fontsize=18)
plt.grid(axis='y')
plt.axhline(0, color='black', linewidth=0.5)  # Baseline at 0 representing the expected proportions
plt.tight_layout()
plt.show()

# Write unmapped predictions to a FASTA file
output = open(
    '../Genome_Processing/Mycoplasma_genitalium_G37/FragGeneScan/FragGeneScan_ART_errFree_Combined_Unmapped_predictions.fasta',
    'w')
for key, value in predictions_without_hit.items():
    output.write('>' + key + '\n' + value + '\n')
