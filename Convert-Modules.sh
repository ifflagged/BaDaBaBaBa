#!/bin/bash

# Ensure the script receives the correct number of arguments
if [[ $# -ne 3 ]]; then
    echo "Usage: $0 <input_file> <module_name> <comment>"
    exit 1
fi

# Input arguments
input_file=$1
module_name=$2
comment=$3

# Output directories
surge_output_dir="Modules/Surge"
loon_output_dir="Modules/Loon"
mkdir -p "$surge_output_dir" "$loon_output_dir"

# Output files
surge_output_file="${surge_output_dir}/${module_name}.sgmodule"
loon_output_file="${loon_output_dir}/${module_name}.plugin"

# Regex patterns to match specific structures
header_regex="^(\^https?:\/\/[^\s]+) (url .*)"
script_path_regex="^(\S+), requires-body\s*=\s*(true|false), tag\s*=\s*(.*)$"
rule_regex="^(HOST.*|IP.*|DOMAIN.*|DOMAIN-SUFFIX.*|DOMAIN-KEYWORD.*|IP-CIDR.*|IP-CIDR6.*)"
url_regex="^(https:\/\/raw\.githubusercontent\.com\/.+)"
mitm_regex="^hostname = (.+)$"

# Function to process header-based rewrites
process_headers() {
    if [[ $1 =~ $header_regex ]]; then
        url_pattern="${BASH_REMATCH[1]}"
        rule_details="${BASH_REMATCH[2]}"
        
        # Determine the type of script and requires-body flag
        if [[ $rule_details =~ script-response|script-echo|script-header ]]; then
            script_type="http-response"
        else
            script_type="http-request"
        fi
        
        # Check if requires-body
        if [[ $rule_details =~ script-response-body|script-request-body|script-analyze ]]; then
            requires_body="requires-body=1"
        else
            requires_body="requires-body=0"
        fi
        
        # Extract script path
        script_url=$(echo "$rule_details" | grep -oE "https:\/\/[^\s]+")
        
        # Write Surge format
        echo "$module_name = type=$script_type,pattern=$url_pattern,$requires_body,script-path=$script_url" >> "$surge_output_file"
        
        # Write Loon format
        echo "$script_type $url_pattern script-path=$script_url, $requires_body, tag=$module_name" >> "$loon_output_file"
    fi
}

# Function to process rule-based rewrites
process_rules() {
    if [[ $1 =~ $rule_regex ]]; then
        rule="${BASH_REMATCH[0]}"
        
        # Write to Surge and Loon formats
        echo "$rule" >> "$surge_output_file"
        echo "$rule" >> "$loon_output_file"
    fi
}

# Function to process MITM
process_mitm() {
    if [[ $1 =~ $mitm_regex ]]; then
        mitm_hosts="${BASH_REMATCH[1]}"
        
        # Write to Surge format
        echo "Hostname = %APPEND% $mitm_hosts" >> "$surge_output_file"
        
        # Write to Loon format
        echo "Hostname = $mitm_hosts" >> "$loon_output_file"
    fi
}

# Function to process URLs
process_urls() {
    if [[ $1 =~ $url_regex ]]; then
        url="${BASH_REMATCH[1]}"
        
        # Convert to GitHub raw format
        surge_url=$(echo "$url" | sed 's/raw.githubusercontent.com/github.com\/raw/')
        
        # Write to Surge and Loon formats
        echo "$surge_url" >> "$surge_output_file"
        echo "$surge_url" >> "$loon_output_file"
    fi
}

# Read and process each line in the input file
while IFS= read -r line; do
    if [[ $line =~ $header_regex ]]; then
        process_headers "$line"
    elif [[ $line =~ $rule_regex ]]; then
        process_rules "$line"
    elif [[ $line =~ $mitm_regex ]]; then
        process_mitm "$line"
    elif [[ $line =~ $url_regex ]]; then
        process_urls "$line"
    else
        # Preserve unhandled lines
        echo "$line" >> "$surge_output_file"
        echo "$line" >> "$loon_output_file"
    fi
done < "$input_file"

echo "Conversion completed! Files saved to:"
echo " - $surge_output_file"
echo " - $loon_output_file"
