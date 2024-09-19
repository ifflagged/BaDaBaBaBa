#!/bin/bash

# Input file containing the data to be processed
input_file=$1
# The name of the module to be used in output
module_name=$2
# Comment tag, not used in processing but added for potential use
comment=$3

# Output files for Surge and Loon
surge_output="Modules/Surge/${module_name}.sgmodule"
loon_output="Modules/Loon/${module_name}.plugin"

# Helper function to process header rewrites
process_header_rewrites() {
    local line=$1
    if [[ "$line" =~ ^\^http.*script-(response-body|echo-response|response-header|request-body|request-header|analyze-echo-response).* ]]; then
        local script_type
        local requires_body

        if [[ "$line" =~ script-(response-body|echo-response|response-header) ]]; then
            script_type="http-response"
            requires_body="true"
        else
            script_type="http-request"
            requires_body="false"
        fi

        # Extract URL and script path
        local pattern=$(echo "$line" | awk '{print $1}')
        local script_url=$(echo "$line" | awk '{print $NF}')

        # Loon format
        echo "$script_type $pattern script-path= $script_url, requires-body = $requires_body, tag = $module_name" >> "$loon_output"

        # Surge format
        local surge_requires_body=$( [[ "$requires_body" == "true" ]] && echo "1" || echo "0" )
        echo "$module_name = type=$script_type,pattern=$pattern,requires-body=$surge_requires_body,script-path=$script_url" >> "$surge_output"
    fi
}

# Helper function to process URL rejections
process_url_rejections() {
    local line=$1
    local pattern=$(echo "$line" | awk '{print $1}')
    local rejection=$(echo "$line" | awk '{print $NF}')

    # Loon format
    echo "$pattern $rejection" >> "$loon_output"

    # Surge format
    echo "$pattern - reject" >> "$surge_output"
}

# Helper function to process rule formats
process_rule_formats() {
    local line=$1
    local rule=$(echo "$line" | sed 's/HOST/DOMAIN/g' | sed 's/HOST-SUFFIX/DOMAIN-SUFFIX/g' | sed 's/HOST-KEYWORD/DOMAIN-KEYWORD/g' | sed 's/IP6-CIDR/IP-CIDR6/g')

    # Handle no-resolve addition for IP-CIDR
    if [[ "$rule" =~ IP-CIDR ]]; then
        rule=$(echo "$rule" | sed 's/IP-CIDR/IP-CIDR, no-resolve/g')
    fi

    # Loon and Surge formats are the same for this case
    echo "$rule" >> "$loon_output"
    echo "$rule" >> "$surge_output"
}

# Helper function to process URLs
process_urls() {
    local line=$1

    # Convert GitHub URLs
    if [[ "$line" =~ githubusercontent ]]; then
        echo "${line/githubusercontent.com/github.com}" >> "$loon_output"
        echo "${line/githubusercontent.com/github.com}" >> "$surge_output"
    fi
}

# Helper function to process MITM hostnames
process_mitm() {
    local line=$1

    # Loon format
    echo "$line" >> "$loon_output"

    # Surge format
    echo "${line/hostname/Hostname = %APPEND%}" >> "$surge_output"
}

# Start processing the input file
while IFS= read -r line; do
    if [[ "$line" =~ script- ]]; then
        process_header_rewrites "$line"
    elif [[ "$line" =~ url ]]; then
        process_url_rejections "$line"
    elif [[ "$line" =~ HOST|IP-CIDR ]]; then
        process_rule_formats "$line"
    elif [[ "$line" =~ https?:// ]]; then
        process_urls "$line"
    elif [[ "$line" =~ hostname ]]; then
        process_mitm "$line"
    else
        # Retain any unprocessed lines in both outputs
        echo "$line" >> "$loon_output"
        echo "$line" >> "$surge_output"
    fi
done < "$input_file"

echo "Processing completed. Files created:"
echo "$loon_output"
echo "$surge_output"
