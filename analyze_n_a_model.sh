#!/bin/bash

# Default input file
INPUT_FILE="pretty.json"

# Check if the default file exists, otherwise prompt for a file
if [ ! -f "$INPUT_FILE" ]; then
    echo "Warning: Default input file '$INPUT_FILE' not found."
    echo "Please specify the input file path:"
    read -p "> " INPUT_FILE
    
    if [ ! -f "$INPUT_FILE" ]; then
        echo "Error: File '$INPUT_FILE' not found. Exiting."
        exit 1
    fi
fi

# This script analyzes the "N/A" model to understand what messages it contains
echo "Analyzing the N/A model using file: $INPUT_FILE"
python analyzer.py --input "$INPUT_FILE" --analyze-model "N/A"

# You can also analyze other models for comparison
echo ""
echo "For comparison, you could also analyze known models with:"
echo "python analyzer.py --input \"$INPUT_FILE\" --analyze-model \"o3\"" 