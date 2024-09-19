#!/bin/bash

input_file=$1
module_name=$2
comment=$3

surge_output_dir="Modules/Surge"
loon_output_dir="Modules/Loon"

# Ensure output directories exist
mkdir -p "$surge_output_dir" "$loon_output_dir"

surge_output_file="$surge_output_dir/${module_name}.sgmodule"
loon_output_file="$loon_output_dir/${module_name}.plugin"

# Start Surge and Loon output files with comments
echo "# $comment" > "$surge_output_file"
echo "# $comment" > "$loon_output_file"

# Function to process each line of the input
process_line() {
    local line="$1"

    # Process header rewrite rules (Format 1 and Format 2)
    if [[ $line =~ ^\^http.*url.*script ]]; then
        # Detect script type for Surge conversion
        if [[ $line =~ script-response-body|script-echo-response|script-response-header ]]; then
            type="http-response"
            requires_body="true"
        elif [[ $line =~ script-request-body|script-analyze-echo-response ]]; then
            type="http-request"
            requires_body="true"
        else
            type="http-request"
            requires_body="false"
        fi

        # Extract URL pattern and script path
        pattern=$(echo "$line" | awk '{print $1}')
        script_url=$(echo "$line" | awk '{print $NF}')

        # Output to Surge format
        echo "=${module_name}= type=${type},pattern=${pattern},requires-body=${requires_body},script-path=${script_url}" >> "$surge_output_file"

        # Output to Loon format
        echo "${type} ${pattern} script-path=${script_url}, requires-body=${requires_body}, tag=${module_name}" >> "$loon_output_file"
    
    # Process URL Rewrite rules
    elif [[ $line =~ ^\^https?:.*url ]]; then
        # Extract URL pattern and action
        pattern=$(echo "$line" | awk '{print $1}')
        action=$(echo "$line" | awk '{print $3}')

        # Output to Surge format
        echo "${pattern} - ${action}" >> "$surge_output_file"

        # Output to Loon format
        echo "${pattern} ${action}" >> "$loon_output_file"
    
    # Process MITM rules
    elif [[ $line =~ ^hostname ]]; then
        # Extract hostname pattern
        hosts=$(echo "$line" | awk -F '=' '{print $2}')

        # Output to Surge format
        echo "Hostname = %APPEND% $hosts" >> "$surge_output_file"

        # Output to Loon format
        echo "Hostname = $hosts" >> "$loon_output_file"
    
    # Process Rule files
    elif [[ $line =~ ^HOST ]]; then
        # Replace HOST format with DOMAIN format for Surge and Loon
        rule=$(echo "$line" | sed -E 's/^HOST/HOST,/' | sed -E 's/;/#/')
        echo "$rule" | sed -E 's/HOST-SUFFIX/DOMAIN-SUFFIX/' \
                      | sed -E 's/HOST-KEYWORD/DOMAIN-KEYWORD/' \
                      | sed -E 's/IP6-CIDR/IP-CIDR6/' \
                      | sed -E 's/REJECT/& no-resolve/' >> "$surge_output_file"
        echo "$rule" >> "$loon_output_file"

    # Process URL links (convert raw to github URLs)
    elif [[ $line =~ https://raw ]]; then
        url=$(echo "$line" | sed 's/raw.githubusercontent.com/github.com\/raw/')
        echo "$url" >> "$surge_output_file"
        echo "$url" >> "$loon_output_file"

    # If the line doesn't match any known patterns, keep it unchanged
    else
        echo "$line" >> "$surge_output_file"
        echo "$line" >> "$loon_output_file"
    fi
}

# Read input file line by line
while IFS= read -r line; do
    process_line "$line"
done < "$input_file"

echo "Conversion completed. Surge output: $surge_output_file, Loon output: $loon_output_file"
