#!/bin/bash

input_file=$1
module_name=$2
comment=$3

# Create output directories if they don't exist
mkdir -p "Modules/Surge"
mkdir -p "Modules/Loon"

# Common replacements for both Surge and Loon
sed_common="\
    /raw.githubusercontent.com/ s/\/main\//\/raw\/main\//Ig; \
    /raw.githubusercontent.com/ s/\/master\//\/raw\/master\//Ig; \
    s/raw.githubusercontent.com/github.com/Ig; \
    s/url script-analyze-echo-response/url script-request-body/Ig; \
    s/HOST,/DOMAIN,/Ig; \
    s/HOST-SUFFIX,/DOMAIN-SUFFIX,/Ig; \
    s/HOST-KEYWORD,/DOMAIN-KEYWORD,/Ig; \
    s/IP-CIDR,/IP-CIDR,/Ig; \
    s/IP6-CIDR,/IP-CIDR6,/Ig; \
    /IP-CIDR/ s/, REJECT/, REJECT, no-resolve/Ig; \
"

# Process the input file line by line
while IFS= read -r line; do
    # Extract tag, type, pattern, and script-path
    tag=$(echo "$line" | grep -oP '(?<=tag = ).*')
    type=$(echo "$line" | grep -oP '^(http-\w+)')
    pattern=$(echo "$line" | grep -oP '(?<=(http-response|http-request) ).*(?= script-path)')
    script_path=$(echo "$line" | grep -oP '(?<=script-path= ).*(?=, requires-body)')
    requires_body=$(echo "$line" | grep -oP '(?<=requires-body = ).*')

    # Convert requires-body to 0/1
    if [ "$requires_body" = "true" ]; then
        requires_body=1
    else
        requires_body=0
    fi

    # Derive module_name from the tag
    module_name="${tag// /_}"

    # Surge conversion
    if [ -n "$tag" ] && [ -n "$pattern" ] && [ -n "$script_path" ] && [ -n "$type" ]; then
        surge_output_file="Modules/Surge/${module_name}.sgmodule"
        echo "$comment" > "$surge_output_file"
        echo "$tag = type=$type,pattern=$pattern,requires-body=$requires_body,script-path=$script_path" >> "$surge_output_file"
        
        # Apply additional Surge-specific replacements
        sed -i \
            -e "$sed_common" \
            -e "s/url reject-200/- reject/Ig" \
            -e 's/url reject/- reject/Ig' \
            "$surge_output_file"
    fi

    # Loon conversion
    if [ -n "$tag" ] && [ -n "$pattern" ] && [ -n "$script_path" ] && [ -n "$type" ]; then
        loon_output_file="Modules/Loon/${module_name}.plugin"
        echo "$comment" > "$loon_output_file"
        echo "$tag = $type $pattern, requires-body = $requires_body, script-path = $script_path" >> "$loon_output_file"

        # Apply additional Loon-specific replacements
        sed -i \
            -e "$sed_common" \
            -e "s/url reject-200/reject-200/Ig" \
            "$loon_output_file"
    fi
done < "$input_file"

echo "Transformation complete. Results saved in the Modules/Surge and Modules/Loon directories."
