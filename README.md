
***

# Human Pathogen Proteome Pipeline

A bioinformatics pipeline to validate, download, and compile reference proteomes for known bacterial human pathogens. The initial dataset is sourced from [Bartlett et al. 2022](https://doi.org/10.1099/mic.0.001269) (*A comprehensive list of bacterial pathogens infecting humans*). The pipeline utilizes the NCBI Datasets CLI to build a unified FASTA database for downstream analysis (e.g., broad-spectrum target discovery via DIAMOND/BLAST).

## 📋 Prerequisites

This pipeline requires `conda` to manage the environment and install both Python dependencies and NCBI tools.

```bash
# Create and activate environment
conda create -n pathogen_db_env -c conda-forge -c bioconda python pandas openpyxl ncbi-datasets-cli unzip diamond
conda activate pathogen_db_env

# (Optional but recommended) Ensure you have the latest NCBI Datasets CLI
conda update -c conda-forge ncbi-datasets-cli
```

## 🚀 Workflow

### 1. Download Pathogen Dataset
Retrieve the compiled list of bacterial human pathogens (pre-2021) from the Bartlett *et al.* repository.

```bash
wget https://github.com/padpadpadpad/bartlett_et_al_2022_human_pathogens/raw/master/data/bacteria_human_pathogens.xlsx
```

### 2. Taxonomy Validation & Cleanup
Biological names change often. This step queries NCBI to map species to official Taxon IDs, applies manual corrections to obsolete names, and drops unresolvable species.

```bash
# 1. Fetch Taxonomy IDs from NCBI (Handles API limits and creates an initial TSV)
python scripts/organism_to_txid_1.py

# 2. Apply manual taxonomy fixes, drop unresolvable species, and finalize dataset
python scripts/organism_to_txid_2.py
```
*Note: Initially, the dataset contained 1,513 organisms (1,110 established, 403 putative). During the automated NCBI query, 15 organisms (7 established, 8 putative) failed to return a Taxon ID. After manual taxonomic checking and correcting, 3 of the "established" pathogens were dropped due to permanently missing/unresolvable IDs. The final verified list contains 1,510 organisms (1,107 established, 403 putative).*

### 3. Target Extraction
Parse the finalized taxonomy dataset to extract only the "established" human pathogens (pathogens known to have infected at least three persons in three or more references).

```bash
python scripts/extract_species.py
# Outputs 1,107 established species to species.txt
```

### 4. Download Proteomes
Execute the download script. This script reads `species.txt`, queries the NCBI Datasets API for the reference genome of each species, and downloads the associated protein `.zip` packages into the `downloads/` directory.

```bash
chmod +x scripts/download_proteomes.sh
scripts/download_proteomes.sh
```
*Note: Progress and errors are tracked in the `logs/` directory.*

```bash
wc -l logs/download_failed.txt # 72
ls downloads | wc -l # 1035
```

### 5. Extract and Combine Proteins
Extract all `.faa` (FASTA amino acid) files from the downloaded archives and merge them into a single `bacteria_human_pathogens.fasta` database. Compress the final file to save space.

```bash
chmod +x scripts/extract_proteins.sh
scripts/extract_proteins.sh

grep -c "^>" bacteria_human_pathogens.fasta # 3454832

# Compress the final sequence database
gzip bacteria_human_pathogens.fasta
```

## 📊 Pipeline Stats (20 April, 2026)
* **Total Original Organisms:** 1,513
* **Final Validated Organisms:** 1,510 (1,107 established, 403 putative)
* **Target Category Extracted:** 1,107 (Established human pathogens)
* **Successful NCBI Downloads:** 1,035
* **Failed Downloads:** 72 *(Species lacking reference proteomes on NCBI)*
* **Total Protein Sequences Extracted:** 3,454,832

## 📂 Project Structure

```text
.
├── downloads/                           # Zipped genome packages from NCBI
├── logs/                                # Tracking success/fails & parsing logs
├── scripts/                             
│   ├── organism_to_txid_1.py            # Fetches initial Taxon IDs
│   ├── organism_to_txid_2.py            # Applies manual taxonomy fixes
│   ├── extract_species.py               # Filters for established pathogens
│   ├── download_proteomes.sh            # NCBI dataset download loop
│   └── extract_proteins.sh              # Fasta extraction and merge script
├── bacteria_human_pathogens.xlsx        # Raw metadata from Bartlett et al.
├── README.md               
├── species.txt                          # Cleaned target list for NCBI downloads
├── bacteria_human_pathogens.fasta       # Extracted FASTA database (if unzipped)
└── bacteria_human_pathogens.fasta.gz    # Compressed final FASTA database
```

## 🛠️ Downstream Usage

```bash
# Example: wget https://github.com/Soash/pathogen-proteome-pipeline/blob/main/bacteria_human_pathogens.fasta.gz
```

The resulting `bacteria_human_pathogens.fasta.gz` can be used for local alignment searches to find broad-spectrum targets. Depending on your tool of choice, you can use standard BLAST or a faster alternative like DIAMOND (which natively supports `.gz` inputs).

### Option A: Using DIAMOND (Recommended for large databases)
DIAMOND is highly recommended for a database of this size (~3.4M sequences). It is significantly faster than standard BLAST and allows you to build the database directly from the compressed file.

```bash
# Build DIAMOND database directly from the .gz file
mkdir -p blast

diamond makedb --in bacteria_human_pathogens.fasta.gz -d blast/pathogen_db

# Run alignment query
diamond blastp -q blast/novel.fasta -d blast/pathogen_db -o blast/results.tsv -f 6
```

### Option B: Using standard BLAST+
If you prefer standard NCBI BLAST, you must uncompress the database first.

```bash
mkdir -p blast

# Unzip for standard BLAST
gunzip -c bacteria_human_pathogens.fasta.gz > blast/bacteria_human_pathogens.fasta

# Build BLAST database
makeblastdb -in blast/bacteria_human_pathogens.fasta -dbtype prot -out blast/pathogen_db

# Run alignment query
blastp -query blast/novel.fasta -db blast/pathogen_db -outfmt 6 -out blast/results.tsv
```