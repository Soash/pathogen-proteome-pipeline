#!/bin/bash

OUTPUT_FILE="bacteria_human_pathogens.fasta"
ZIP_DIR="downloads"

# Clear the output file if it already exists so we don't append to old data
> "$OUTPUT_FILE"

echo "Starting extraction..."

# Loop through all zip files in the downloads directory
for zip_file in "$ZIP_DIR"/*.zip; do
    if [ -f "$zip_file" ]; then
        # Print the name of the file being processed (optional, for tracking progress)
        echo "Extracting from: $(basename "$zip_file")"
        
        # -p extracts to standard output. 
        # The quotes around the internal path prevent the shell from expanding the wildcard too early.
        # We append (>>) the output to our final database file.
        # 2>/dev/null hides warnings if a specific zip somehow doesn't contain a protein.faa
        unzip -p "$zip_file" "ncbi_dataset/data/*/protein.faa" >> "$OUTPUT_FILE" 2>/dev/null
    fi
done

echo "✅ All done! Combined database saved as $OUTPUT_FILE"


