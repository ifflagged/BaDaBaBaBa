#!/bin/bash

input_file=$1
module_name=$2
comment=$3

# Output directories for Surge and Loon
surge_output="Modules/Surge/${module_name}.sgmodule"
loon_output="Modules/Loon/${module_name}.plugin"

# Ensure the output directories exist
mkdir -p "$(dirname "$surge_output")" "$(dirname "$loon_output")"

# Initialize the output files
echo "# ${comment}" > "$surge_output"
echo "# ${comment}" > "$loon_output"

# Function to handle Header Rewrite
process_header_rewrite() {
    local line="$1"
    local pattern
    local url
    local requires_body

    if [[ $line =~ ^http ]]; then
        pattern=$(echo "$line" | awk '{print $1}')
        url=$(echo "$line" | awk '{print $4}')
    else
        pattern=$(echo "$line" | awk '{print $2}')
        url=$(echo "$line" | awk '{print $5}')
    fi

    # Detect request/response type and requires-body
    if [[ $line =~ script-response-body|script-echo-response|script-response-header|script-request-body|script-analyze-echo-response ]]; then
        requires_body="requires-body=1"
    else
        requires_body="requires-body=0"
    fi

    # Write to Surge output
    echo "${module_name} = type=$(echo "$line" | grep -oP 'http-response|http-request'),pattern=${pattern},${requires_body},script-path=${url}" >> "$surge_output"

    # Write to Loon output
    echo "$(echo "$line" | grep -oP 'http-response|http-request') ${pattern} script-path=${url}, ${requires_body/0/false}, ${requires_body/1/true}, tag=${module_name}" >> "$loon_output"
}

# Function to handle URL Rewrite
process_url_rewrite() {
    local line="$1"
    local pattern=$(echo "$line" | awk '{print $1}')
    local action=$(echo "$line" | awk '{print $3}')

    # Convert to Surge format
    echo "${pattern} - ${action/reject*/reject}" >> "$surge_output"

    # Convert to Loon format
    echo "${pattern} ${action}" >> "$loon_output"
}

# Function to handle Rule
process_rule() {
    local line="$1"
    local type=$(echo "$line" | awk -F', ' '{print $1}')
    local domain=$(echo "$line" | awk -F', ' '{print $2}')
    local action=$(echo "$line" | awk -F', ' '{print $3}')

    # Handle Surge and Loon conversion
    case $type in
        HOST|HOST-SUFFIX|HOST-KEYWORD)
            echo "DOMAIN${type/HOST/}, ${domain}, ${action}" >> "$surge_output"
            echo "DOMAIN${type/HOST/}, ${domain}, ${action}" >> "$loon_output"
            ;;
        IP-CIDR)
            echo "IP-CIDR, ${domain}, ${action}, no-resolve" >> "$surge_output"
            echo "IP-CIDR, ${domain}, ${action}" >> "$loon_output"
            ;;
        IP6-CIDR)
            echo "IP-CIDR6, ${domain}, ${action}" >> "$surge_output"
            echo "IP-CIDR6, ${domain}, ${action}" >> "$loon_output"
            ;;
        *)
            echo "# Ignored: ${line}" >> "$surge_output"
            echo "# Ignored: ${line}" >> "$loon_output"
            ;;
    esac
}

# Function to handle URLs
process_url() {
    local line="$1"
    local new_url=$(echo "$line" | sed -E 's/raw\.githubusercontent\.com/github.com\/raw/g')
    echo "$new_url" >> "$surge_output"
    echo "$new_url" >> "$loon_output"
}

# Function to handle MITM
process_mitm() {
    local line="$1"
    local hosts=$(echo "$line" | awk -F'=' '{print $2}')

    # Write to Surge and Loon
    echo "Hostname = %APPEND% ${hosts}" >> "$surge_output"
    echo "Hostname = ${hosts}" >> "$loon_output"
}

# Read the input file line by line and process it
while IFS= read -r line; do
    # Skip empty lines
    [[ -z "$line" ]] && continue

    if [[ $line =~ ^http ]]; then
        process_header_rewrite "$line"
    elif [[ $line =~ url ]]; then
        process_url_rewrite "$line"
    elif [[ $line =~ ^HOST|IP|^;HOST ]]; then
        process_rule "$line"
    elif [[ $line =~ ^https ]]; then
        process_url "$line"
    elif [[ $line =~ ^hostname ]]; then
        process_mitm "$line"
    fi
done < "$input_file"

echo "Conversion complete: Surge -> $surge_output, Loon -> $loon_output"
