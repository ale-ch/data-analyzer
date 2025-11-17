
#!/usr/bin/env bash
set -e

# Directory where your Snakefile lives (fixed location)
PIPELINE_DIR="/Users/work/Documents/Programming/test/data-analyzer"

# Run Snakemake so that the work directory is where run.sh is launched
snakemake \
    -s "$PIPELINE_DIR/Snakefile" \
    --directory "$PWD" \
    --use-conda \
    -j1

