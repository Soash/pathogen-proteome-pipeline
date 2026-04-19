#!/bin/bash

# -------------------------------
# Config
# -------------------------------
SUCCESS_LOG="logs/download_success.txt"
FAILED_LOG="logs/download_failed.txt"
MULTI_OR_NONE_LOG="logs/not_exactly_one_genome.txt"
OUTPUT_DIR="downloads"
LOG_FILE="logs/download_log.txt"
INPUT_FILE="species.txt"

mkdir -p "$OUTPUT_DIR"
mkdir -p "logs"
# -------------------------------
# Main loop
# -------------------------------
TOTAL_SPECIES=$(wc -l < "$INPUT_FILE")
CURRENT=0

while read -r sp; do
  ((CURRENT++))
  echo "Progress: $CURRENT/$TOTAL_SPECIES"
  # Convert space to underscore for filename
  fname=$(echo "$sp" | tr ' ' '_')
  outfile="$OUTPUT_DIR/${fname}.zip"

  # Skip already downloaded files
  if [ -f "$outfile" ]; then
    echo "⏩ Skipping (already exists): $sp"
    continue
  fi

  echo "🚀 Downloading: $sp"

  # Download using NCBI datasets CLI and capture output
  output=$(datasets download genome taxon "$sp" \
    --reference \
    --include protein \
    --filename "$outfile" 2>&1)

  # -------------------------------
  # Clean output for logging (remove ANSI escape sequences)
  # -------------------------------
  clean_output=$(echo "$output" | sed -r "s/\x1B\[[0-9;]*[a-zA-Z]//g" | tr -d '\r')

  # Save to log
  echo "----- $sp -----" >> "$LOG_FILE"
  echo "$clean_output" >> "$LOG_FILE"

  # Extract number of genomes collected (only first match)
  collected=$(echo "$clean_output" | grep -oP 'Collecting \K[0-9]+(?= genome record)' | head -n1)

  # -------------------------------
  # Check download result
  # -------------------------------
  if echo "$clean_output" | grep -q "valid data package"; then
    if [ "$collected" -eq 1 ]; then
      # Success: exactly 1 genome
      echo "$sp" >> "$SUCCESS_LOG"
      echo "✅ Success: $sp"
    else
      # Valid package but not exactly 1 genome
      echo "$sp (collected=$collected)" >> "$MULTI_OR_NONE_LOG"
      echo "💥 Not exactly 1 genome: $sp (collected=$collected)"
      echo "$sp" >> "$SUCCESS_LOG"
      echo "✅ Success: $sp"
    fi
  else
    # ❌ Failed download
    echo "$sp" >> "$FAILED_LOG"
    echo "❌ Failed download: $sp"
  fi

done < "$INPUT_FILE"

echo "🎉 All done! Check logs for details:"
echo "  ✅ Success: $SUCCESS_LOG"
echo "  💥 Not exactly one genome: $MULTI_OR_NONE_LOG"
echo "  ❌ Failed downloads: $FAILED_LOG"








