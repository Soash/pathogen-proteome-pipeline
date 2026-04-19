import pandas as pd
import logging
import os

# --- Setup Logging ---
# Will use the existing logs/ folder in your root directory
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/extract_species.log"),
        logging.StreamHandler()
    ]
)

def main():
    input_file = "results/organism_to_txid_final.tsv"
    output_file = "species.txt"

    logging.info(f"Reading target file: {input_file}")
    try:
        df = pd.read_table(input_file)
    except FileNotFoundError:
        logging.error(f"File {input_file} not found. Ensure you are running this from the root directory.")
        return

    logging.info(f"Dataset shape loaded: {df.shape}")
    logging.info(f"Status distribution:\n{df['status'].value_counts().to_string()}")

    logging.info("Filtering dataset for 'established' species...")
    established_df = df[df["status"] == "established"]

    logging.info(f"Writing {len(established_df)} species to {output_file}...")
    established_df["organism"].to_csv(output_file, index=False, header=False)

    logging.info("Extraction complete! The species list is ready for downloading proteomes.")

if __name__ == "__main__":
    main()



    