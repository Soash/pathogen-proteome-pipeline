import pandas as pd
import logging
import os

# --- Setup Logging ---
# Creates a logs directory inside the organism_to_txid folder if it doesn't exist
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/organism_fixer.log"),
        logging.StreamHandler()
    ]
)

def main():
    file_in = "results/organism_to_txid_initial.tsv"
    file_out = "results/organism_to_txid_final.tsv"

    logging.info(f"Loading initial dataset from: {file_in}")
    try:
        df = pd.read_csv(file_in, sep="\t", dtype={'txid': str})
    except FileNotFoundError:
        logging.error(f"File {file_in} not found. Please run organism_to_txid_1.py first.")
        return

    logging.info(f"Initial Status Distribution:\n{df['status'].value_counts().to_string()}")

    # 1. Define manual fixes dictionary
    manual_fixes = {
        # established
        "Eubacterium cylindroides": ("Faecalitalea cylindroides", "39483"), # Homotypic synonyms
        "Eubacterium moniliforme": ("Clostridium moniliforme", "39489"), # Homotypic synonyms
        "Streptococcus sanguis": ("Streptococcus sanguinis", "1305"), # Spelling correction
        "Propionibacterium propionicum": ("Arachnia propionica", "1750"), # Homotypic synonyms

        # putative
        "Tsukamurella strandjordae": ("Tsukamurella strandjordii", "147577"),
        "Bacteroides denticanum": ("Bacteroides denticanium", "266833"),
        "Chitinophaga terrae": ("Chitinophaga terrae", "408074"),
        "Pseudoclavibacter bifida": ("Gulosibacter bifidus", "272239"),

        "Vibrio injenensis": ("Vibrio injensis", "1307414"),
        "Campylobacter infans": ("Candidatus Campylobacter infans", "2561898"),
        "Megasphaera vaginalis": ("Megasphaera vaginalis", "2045301"),
        "Parapseudoflavitalea muciniphila": ("Pseudoflavitalea muciniphila", "2100819")
    }

    # 2. Apply manual updates
    logging.info("Applying manual taxonomy fixes...")
    for old_org, (new_org, new_txid) in manual_fixes.items():
        mask = df['organism'] == old_org
        if mask.any():
            df.loc[mask, 'organism'] = new_org
            df.loc[mask, 'txid'] = new_txid
            df.loc[mask, 'source'] = 'manual'
            logging.info(f"  Fixed: {old_org} -> {new_org} (TXID: {new_txid})")
        else:
            logging.warning(f"  Organism not found for fix: {old_org}")

    # 3. Define organisms to drop
    organisms_to_drop = [
        "Rickettsia xinyangensis", # Cannot yet be cultured in a laboratory
        "Treponema carateum", # Cannot yet be cultured in a laboratory
        "Propionibacterium granulosum" # Cutibacterium granulosum already has a valid Taxonomy ID, Homotypic synonyms
    ]

    # 4. Drop them cleanly AND log their status
    logging.info("Dropping unresolved organisms:")
    for org in organisms_to_drop:
        mask = df['organism'] == org
        if mask.any():
            # Extract the status of the organism being dropped
            org_status = df.loc[mask, 'status'].iloc[0]
            logging.info(f"  Dropped: {org} (Status: {org_status})")
        else:
            logging.warning(f"  Organism not found for dropping: {org}")

    # Actually remove them from the dataframe
    df = df[~df['organism'].isin(organisms_to_drop)]

    # 5. QA Checks
    duplicate_count = df.duplicated(subset=['organism']).sum()
    if duplicate_count > 0:
        logging.warning(f"Found {duplicate_count} duplicate organism(s)!")
    else:
        logging.info("No duplicates found in the dataset.")

    missing_txid_count = len(df[df['txid'].isna()])
    logging.info(f"Organisms remaining with missing TXIDs: {missing_txid_count}")
    logging.info(f"Final dataset shape: {df.shape}")

    # 6. Save final file
    df.to_csv(file_out, sep="\t", index=False)
    logging.info(f"All manual fixes applied! Final clean dataset saved to {file_out}.")

if __name__ == "__main__":
    main()