#!/bin/bash

input_file=$1
module_name=$2
comment=$3

# Output directories for Surge and Loon
surge_output_dir="Modules/Surge"
loon_output_dir="Modules/Loon"

# Create the output directories if they don't exist
mkdir -p $surge_output_dir
mkdir -p $loon_output_dir

surge_output_file="${surge_output_dir}/${module_name}.sgmodule"
loon_output_file="${loon_output_dir}/${module_name}.plugin"

# Function to process each line and convert to Surge/Loon format
process_line() {
    line=$1
    surge_line=""
    loon_line=""

    # Header Rewrite matching
    if [[ $line =~ ^(.*)\ url\ (script-(response|request|echo)-body|script-(response|request|analyze)-header)\ (https.*\.js)$ ]]; then
        url_pattern="${BASH_REMATCH[1]}"
        script_type="${BASH_REMATCH[2]}"
        script_url="${BASH_REMATCH[4]}"
        
        # Determine if it needs requires-body
        if [[ "$script_type" =~ ^(script-response-body|script-echo-response|script-response-header|script-request-body|script-analyze-echo-response)$ ]]; then
            requires_body="1"
        else
            requires_body="0"
        fi

        # Convert to Surge format
        if [[ "$script_type" =~ ^script-response ]]; then
            surge_line="${module_name} = type=http-response,pattern=${url_pattern},requires-body=${requires_body},script-path=${script_url}"
        else
            surge_line="${module_name} = type=http-request,pattern=${url_pattern},requires-body=${requires_body},script-path=${script_url}"
        fi
        
        # Convert to Loon format
        if [[ "$script_type" =~ ^script-response ]]; then
            loon_line="http-response ${url_pattern} script-path=${script_url}, requires-body=${requires_body}, tag=${module_name}"
        else
            loon_line="http-request ${url_pattern} script-path=${script_url}, requires-body=${requires_body}, tag=${module_name}"
        fi

    # URL Rewrite matching
    elif [[ $line =~ ^(\^https?.*)\ url\ reject.*$ ]]; then
        url_pattern="${BASH_REMATCH[1]}"
        
        # Convert to Surge format
        surge_line="${url_pattern} - reject"
        
        # Convert to Loon format
        loon_line="${line}"

    # Rule matching
    elif [[ $line =~ ^(HOST|HOST-SUFFIX|HOST-KEYWORD|IP-CIDR|IP6-CIDR), ]]; then
        surge_line=$(echo $line | sed 's/HOST/DOMAIN/g' | sed 's/IP6-CIDR/IP-CIDR6/g' | sed 's/$/, no-resolve/')
        loon_line=$(echo $line | sed 's/HOST/DOMAIN/g' | sed 's/IP6-CIDR/IP-CIDR6/g')
    
    # URL conversion (raw URLs to Surge/Loon compatible URLs)
    elif [[ $line =~ ^(https:\/\/raw\.githubusercontent\.com\/.*)$ ]]; then
        surge_line=$(echo $line | sed 's/raw\.githubusercontent\.com/github.com\/raw/')
        loon_line=$(echo $line | sed 's/raw\.githubusercontent\.com/github.com\/raw/')
    
    # MITM hostname matching
    elif [[ $line =~ ^hostname\ =\ (.*)$ ]]; then
        hosts="${BASH_REMATCH[1]}"
        
        # Convert to Surge format
        surge_line="Hostname = %APPEND% ${hosts}"
        
        # Convert to Loon format
        loon_line="Hostname = ${hosts}"
    fi

    # Append the results to the Surge and Loon files
    if [[ -n $surge_line ]]; then
        echo "$surge_line" >> $surge_output_file
    fi
    if [[ -n $loon_line ]]; then
        echo "$loon_line" >> $loon_output_file
    fi
}

# Read the input file line by line and process it
while IFS= read -r line; do
    process_line "$line"
done < "$input_file"

echo "Conversion complete! Output files:"
echo "Surge: $surge_output_file"
echo "Loon: $loon_output_file"
