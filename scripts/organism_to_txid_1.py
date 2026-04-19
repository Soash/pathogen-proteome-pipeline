import os
import json
import subprocess
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Configuration ---
INPUT_FILE = 'bacteria_human_pathogens.xlsx'
SHEET_NAME = 'Tab 6 Full List'
OUTPUT_FILE = 'results/organism_to_txid_initial.tsv'
MAX_WORKERS = 8
TIMEOUT_SECONDS = 10

def clean_text(text):
    """Removes hidden characters and non-ASCII artifacts."""
    if pd.isna(text):
        return ""
    # Drop non-ASCII characters and strip surrounding whitespace
    cleaned = str(text).encode('ascii', 'ignore').decode('ascii').strip()
    return cleaned

def fetch_txid(organism):
    """Fetches the taxonomic ID using NCBI datasets CLI with a timeout guard."""
    try:
        result = subprocess.run(
            ["datasets", "summary", "taxonomy", "taxon", organism],
            capture_output=True, 
            text=True, 
            check=True,
            timeout=TIMEOUT_SECONDS # Prevents hanging if the server rate-limits you
        )
        data = json.loads(result.stdout)
        
        # Verify reports exist in the JSON structure
        if "reports" in data and len(data["reports"]) > 0:
            report = data["reports"][0]["taxonomy"]
            txid = report["tax_id"]
            return str(txid), "ncbi_datasets"
        else:
            raise ValueError("No reports found")
            
    except Exception as e:
        # If the CLI fails, times out, or no report is found, return strict N/A
        return "N/A", "N/A"

def main():
    print("Loading original Excel file...")
    # 1. Load the Excel file
    df = pd.read_excel(INPUT_FILE, sheet_name=SHEET_NAME)

    # 2. Clean text and create the target 'organism' column
    df['genus'] = df['genus'].apply(clean_text)
    df['species'] = df['species'].apply(clean_text)
    df['organism'] = df['genus'] + " " + df['species']

    # 3. Initialize tracking columns
    df['txid'] = pd.NA
    df['source'] = pd.NA

    # 4. Resumability Logic
    if os.path.exists(OUTPUT_FILE):
        print(f"Found existing {OUTPUT_FILE}. Loading previous progress...")
        
        # Read the file. keep_default_na=False ensures "N/A" stays "N/A", but turns blanks into ""
        df_existing = pd.read_csv(OUTPUT_FILE, sep="\t", keep_default_na=False)
        
        # Temporarily set 'organism' as the index to align and update the dataframes
        df.set_index('organism', inplace=True)
        df_existing.set_index('organism', inplace=True)
        
        # Update our main dataframe with the previously fetched values
        df.update(df_existing)
        
        # Reset the index back to normal
        df.reset_index(inplace=True)
        print("Progress successfully loaded.")

    # 5. Filter organisms that still need processing
    # NEW FIX: We convert the column to a string, strip it, and look for "", "N/A", or "nan".
    # This guarantees that previously failed "N/A" rows are selected for a retry!
    txid_str = df['txid'].astype(str).str.strip()
    missing_mask = df['txid'].isna() | txid_str.isin(["", "N/A", "<NA>", "nan"])
    
    organisms_to_process = df[missing_mask]['organism'].unique().tolist()
    
    print(f"Remaining organisms to process (including 'N/A' retries): {len(organisms_to_process)}")

    # 6. Execute parallel fetching
    if len(organisms_to_process) > 0:
        print(f"Starting ThreadPoolExecutor with {MAX_WORKERS} workers...")
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_org = {executor.submit(fetch_txid, org): org for org in organisms_to_process}
            
            for future in as_completed(future_to_org):
                org = future_to_org[future]
                txid, source = future.result()

                print(f"Organism: {org} | TXID: {txid} | Source: {source}")

                # Update the main dataframe in memory
                mask = df["organism"] == org
                df.loc[mask, "txid"] = txid
                df.loc[mask, "source"] = source

                # 7. Dynamically select columns for output and save incrementally
                output_cols = ["organism", "status", "txid", "source"]
                
                # Fallback to ensure we don't crash if 'status' isn't in the input file
                if "status" not in df.columns:
                    output_cols.remove("status")
                    
                output_df = df[output_cols]
                output_df.to_csv(OUTPUT_FILE, sep="\t", index=False)
                
        print("\nFetching complete! All data saved to", OUTPUT_FILE)
    else:
        print("All organisms have successfully been assigned an ID. Output is up to date.")

if __name__ == "__main__":
    main()


    