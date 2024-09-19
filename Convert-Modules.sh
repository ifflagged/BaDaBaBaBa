#!/bin/bash

input_file=$1
module_name=$2
comment=$3

surge_output="Modules/Surge/${module_name}.sgmodule"
loon_output="Modules/Loon/${module_name}.plugin"

# Create output directories if they don't exist
mkdir -p "Modules/Surge"
mkdir -p "Modules/Loon"

# Initialize output files
echo "# Surge module for $module_name" > "$surge_output"
echo "# Loon module for $module_name" > "$loon_output"

# Function to process Header Rewrite
process_header_rewrite() {
    local line="$1"

    # Match and process Header Rewrite
    if [[ $line =~ ^\^http ]]; then
        url=$(echo "$line" | awk '{print $1}')
        type=$(echo "$line" | awk '{print $2}')
        script_url=$(echo "$line" | awk '{print $4}')

        # Determine the type of request and requires-body
        if [[ $type == "script-response-body" || $type == "script-echo-response" || $type == "script-response-header" ]]; then
            echo "$module_name = type=http-response,pattern=${url},requires-body=1,script-path=${script_url}" >> "$surge_output"
            echo "http-response ${url} script-path=${script_url}, requires-body = true, tag = $module_name" >> "$loon_output"
        else
            echo "$module_name = type=http-request,pattern=${url},requires-body=0,script-path=${script_url}" >> "$surge_output"
            echo "http-request ${url} script-path=${script_url}, requires-body = false, tag = $module_name" >> "$loon_output"
        fi
    fi
}

# Function to process URL Rewrite
process_url_rewrite() {
    local line="$1"

    # Match and process URL Rewrite
    if [[ $line =~ ^\^https?: ]]; then
        url=$(echo "$line" | awk '{print $1}')
        reject_type=$(echo "$line" | awk '{print $3}')

        # Process for Surge and Loon formats
        echo "${url} - reject" >> "$surge_output"
        echo "${url} $reject_type" >> "$loon_output"
    fi
}

# Function to process Rule
process_rule() {
    local line="$1"

    # Match and process Rule
    if [[ $line =~ ^HOST ]]; then
        echo "DOMAIN, ${line:6}, REJECT" >> "$surge_output"
        echo "DOMAIN, ${line:6}, REJECT" >> "$loon_output"
    elif [[ $line =~ ^HOST-SUFFIX ]]; then
        echo "DOMAIN-SUFFIX, ${line:12}, REJECT" >> "$surge_output"
        echo "DOMAIN-SUFFIX, ${line:12}, REJECT" >> "$loon_output"
    elif [[ $line =~ ^HOST-KEYWORD ]]; then
        echo "DOMAIN-KEYWORD, ${line:13}, REJECT" >> "$surge_output"
        echo "DOMAIN-KEYWORD, ${line:13}, REJECT" >> "$loon_output"
    elif [[ $line =~ ^IP-CIDR ]]; then
        echo "IP-CIDR, ${line:8}, REJECT, no-resolve" >> "$surge_output"
        echo "IP-CIDR, ${line:8}, REJECT" >> "$loon_output"
    elif [[ $line =~ ^IP6-CIDR ]]; then
        echo "IP-CIDR6, ${line:9}, REJECT" >> "$surge_output"
        echo "IP-CIDR6, ${line:9}, REJECT" >> "$loon_output"
    fi
}

# Function to process URLs
process_url() {
    local line="$1"

    # Convert URL formats
    if [[ $line =~ https ]]; then
        new_url=$(echo "$line" | sed 's/raw.githubusercontent.com/github.com\/RuCu6\/QuanX\/raw/')
        echo "$new_url" >> "$surge_output"
        echo "$new_url" >> "$loon_output"
    fi
}

# Function to process MITM
process_mitm() {
    local line="$1"

    # Convert MITM format
    if [[ $line =~ ^hostname ]]; then
        mitm_domains=$(echo "$line" | sed 's/hostname = //')
        echo "Hostname = %APPEND% $mitm_domains" >> "$surge_output"
        echo "Hostname = $mitm_domains" >> "$loon_output"
    fi
}

# Read the input file line by line and process it
while IFS= read -r line; do
    # Skip empty lines
    [[ -z "$line" ]] && continue

    if [[ $line =~ ^http ]]; then
        process_header_rewrite "$line"
    elif [[ $line =~ url ]]; then
        process_url_rewrite "$line"
    elif [[ $line =~ ^HOST || $line =~ ^IP || $line =~ ^";HOST" ]]; then
        process_rule "$line"
    elif [[ $line =~ ^https ]]; then
        process_url "$line"
    elif [[ $line =~ ^hostname ]]; then
        process_mitm "$line"
    fi
done < "$input_file"

echo "Conversion complete. Output files:"
echo "$surge_output"
echo "$loon_output"
