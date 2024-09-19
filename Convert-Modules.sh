#!/bin/bash

input_file=$1
module_name=$2
comment=$3

# Output paths
surge_output="Modules/Surge/${module_name}.sgmodule"
loon_output="Modules/Loon/${module_name}.plugin"

# Create output directories if they don't exist
mkdir -p Modules/Surge
mkdir -p Modules/Loon

# Initialize output files
echo "# Surge module for ${module_name}" > "$surge_output"
echo "# Loon plugin for ${module_name}" > "$loon_output"

# Function to handle rewrites and convert formats
convert_rewrite() {
    local line="$1"

    # Check for script-response-body, script-echo-response, etc.
    if [[ $line =~ script-response-body|script-echo-response|script-response-header ]]; then
        requires_body="requires-body=1"
        type="http-response"
    elif [[ $line =~ script-request-body|script-analyze-echo-response ]]; then
        requires_body="requires-body=1"
        type="http-request"
    else
        requires_body="requires-body=0"
        if [[ $line =~ http-response ]]; then
            type="http-response"
        else
            type="http-request"
        fi
    fi

    # Extract pattern and script path from the input line
    pattern=$(echo "$line" | cut -d' ' -f1)
    script_path=$(echo "$line" | grep -oP '(https?://[^\s]+)')

    # Write to Surge format
    echo "${module_name} = type=${type},pattern=${pattern},${requires_body},script-path=${script_path}" >> "$surge_output"

    # Write to Loon format
    echo "${type} ${pattern} script-path=${script_path}, ${requires_body}, tag=${module_name}" >> "$loon_output"
}

# Function to handle URL rejections and convert formats
convert_url_reject() {
    local line="$1"

    # Extract pattern and reject type
    pattern=$(echo "$line" | cut -d' ' -f1)

    # Surge output format
    echo "${pattern} - reject" >> "$surge_output"

    # Loon output format
    echo "${pattern} reject" >> "$loon_output"
}

# Function to handle Rule section
convert_rule() {
    local line="$1"
    # Convert HOST to DOMAIN and apply other transformations for Surge and Loon
    converted_line=$(echo "$line" | sed 's/HOST/DOMAIN/g; s/HOST-SUFFIX/DOMAIN-SUFFIX/g; s/HOST-KEYWORD/DOMAIN-KEYWORD/g; s/IP6-CIDR/IP-CIDR6/g')
    
    # Surge output format
    echo "$converted_line" >> "$surge_output"
    
    # Loon output format
    echo "$converted_line" >> "$loon_output"
}

# Function to handle URL section
convert_url() {
    local line="$1"
    
    # Convert raw.githubusercontent URL to the Surge/Loon format
    converted_url=$(echo "$line" | sed 's/raw.githubusercontent.com/github.com/g' | sed 's/\/raw\//\/blob\//g')

    # Write to both Surge and Loon outputs
    echo "$converted_url" >> "$surge_output"
    echo "$converted_url" >> "$loon_output"
}

# Function to handle MITM hostname section
convert_mitm() {
    local line="$1"

    # Surge format (append mode)
    echo "Hostname = %APPEND% ${line}" >> "$surge_output"

    # Loon format
    echo "Hostname = ${line}" >> "$loon_output"
}

# Process the input file line by line
while IFS= read -r line; do
    case "$line" in
        # Detect header rewrites and process
        Header\ Rewrite*)
            convert_rewrite "$line"
            ;;
        # Detect URL rewrites and process
        URL\ Rewrite*)
            convert_url_reject "$line"
            ;;
        # Detect rules and process
        Rule*)
            convert_rule "$line"
            ;;
        # Detect URLs and process
        URL*)
            convert_url "$line"
            ;;
        # Detect MITM hostnames and process
        MITM*)
            convert_mitm "$line"
            ;;
        *)
            echo "Unknown line format: $line"
            ;;
    esac
done < "$input_file"

echo "Conversion complete. Output files:"
echo "Surge: $surge_output"
echo "Loon: $loon_output"
