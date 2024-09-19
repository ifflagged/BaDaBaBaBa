#!/bin/bash

input_file=$1
module_name=$2
comment=$3

# Output directories
surge_output_dir="Modules/Surge"
loon_output_dir="Modules/Loon"

# Create directories if they don't exist
mkdir -p "$surge_output_dir" "$loon_output_dir"

surge_output="${surge_output_dir}/${module_name}.sgmodule"
loon_output="${loon_output_dir}/${module_name}.plugin"

# Function to process QX Header Rewrite and convert to Surge/Loon formats
process_header_rewrite() {
    while read -r line; do
        # Extract details based on QuanX format and convert
        pattern=$(echo "$line" | awk '{print $1}')
        type=$(echo "$line" | awk '{print $3}')
        url=$(echo "$line" | awk '{print $5}')
        
        # Determine request type and requires-body
        case "$type" in
            "script-response-body"|"script-echo-response"|"script-response-header")
                surge_type="http-response"
                loon_type="http-response"
                requires_body=1
                ;;
            "script-request-body"|"script-analyze-echo-response")
                surge_type="http-request"
                loon_type="http-request"
                requires_body=0
                ;;
            *)
                surge_type="http-request"
                loon_type="http-request"
                requires_body=0
                ;;
        esac

        # Write to Surge output
        echo "$module_name = type=${surge_type},pattern=${pattern},requires-body=${requires_body},script-path=${url}" >> "$surge_output"
        
        # Write to Loon output
        echo "${loon_type} ${pattern} script-path=${url}, requires-body=${requires_body}, tag=${module_name}" >> "$loon_output"
    done < <(grep '^http' "$input_file") # Filter lines starting with URLs
}

# Function to process QX URL Rewrite and convert to Surge/Loon formats
process_url_rewrite() {
    while read -r line; do
        # Extract details
        pattern=$(echo "$line" | awk '{print $1}')
        qx_action=$(echo "$line" | awk '{print $3}')

        # Convert action for Surge and Loon
        surge_action="reject"
        loon_action=$qx_action
        
        # Write to Surge output
        echo "$pattern - $surge_action" >> "$surge_output"
        
        # Write to Loon output
        echo "$pattern $loon_action" >> "$loon_output"
    done < <(grep '^https?' "$input_file") # Filter lines starting with http/https patterns
}

# Function to process Rules
process_rules() {
    while read -r line; do
        # Extract details
        rule_type=$(echo "$line" | awk -F', ' '{print $1}')
        domain=$(echo "$line" | awk -F', ' '{print $2}')
        action=$(echo "$line" | awk -F', ' '{print $3}')
        
        # Convert to Surge and Loon formats
        if [[ "$rule_type" == "HOST" ]]; then
            surge_rule="DOMAIN, ${domain}, ${action}"
            loon_rule="DOMAIN, ${domain}, ${action}"
        else
            surge_rule="${rule_type}, ${domain}, ${action}, no-resolve"
            loon_rule="${rule_type}, ${domain}, ${action}"
        fi
        
        # Write to Surge output
        echo "$surge_rule" >> "$surge_output"
        
        # Write to Loon output
        echo "$loon_rule" >> "$loon_output"
    done < <(grep '^HOST' "$input_file") # Filter lines starting with HOST rules
}

# Function to process MITM entries
process_mitm() {
    while read -r line; do
        # Process MITM hostnames
        mitm_hosts=$(echo "$line" | awk -F' = ' '{print $2}')
        
        # Append for Surge
        echo "Hostname = %APPEND% ${mitm_hosts}" >> "$surge_output"
        
        # Regular format for Loon
        echo "Hostname = ${mitm_hosts}" >> "$loon_output"
    done < <(grep '^hostname' "$input_file")
}

# Run the functions to process different types
process_header_rewrite
process_url_rewrite
process_rules
process_mitm

echo "Conversion completed. Files saved to $surge_output and $loon_output."
