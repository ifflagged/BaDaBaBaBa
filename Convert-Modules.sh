#!/bin/bash

# Input and output variables
input_file=$1
module_name=$2
comment=$3

# Create directories for Surge and Loon if not already present
mkdir -p Modules/Surge Modules/Loon

# Output files for Surge and Loon
surge_output="Modules/Surge/${module_name}.sgmodule"
loon_output="Modules/Loon/${module_name}.plugin"

# Initialize output files
echo "# Surge format for ${module_name}" > "$surge_output"
echo "# Loon format for ${module_name}" > "$loon_output"

# Read the input file line by line
while IFS= read -r line; do

    # Rewrite processing (Surge & Loon)
    if [[ "$line" =~ ^(http|https)-response.*script-path ]]; then
        # Convert to Surge format
        converted_surge=$(echo "$line" | sed -E 's/(http.*response.*)(script-path)/type=http-response,\1requires-body=1,\2/')
        echo "$converted_surge" >> "$surge_output"

        # Convert to Loon format
        converted_loon=$(echo "$line" | sed -E 's/(http.*response.*)(script-path)/\1, requires-body=true, tag = '"${module_name}"'/')
        echo "$converted_loon" >> "$loon_output"

    elif [[ "$line" =~ ^(http|https)-request.*script-path ]]; then
        # Convert to Surge format
        converted_surge=$(echo "$line" | sed -E 's/(http.*request.*)(script-path)/type=http-request,\1requires-body=0,\2/')
        echo "$converted_surge" >> "$surge_output"

        # Convert to Loon format
        converted_loon=$(echo "$line" | sed -E 's/(http.*request.*)(script-path)/\1, requires-body=false, tag = '"${module_name}"'/')
        echo "$converted_loon" >> "$loon_output"

    # URL Rewrite processing
    elif [[ "$line" =~ ^(http|https).*url.*reject ]]; then
        # Convert to Surge and Loon format
        converted=$(echo "$line" | sed 's/url reject/- reject/')
        echo "$converted" >> "$surge_output"
        echo "$line" >> "$loon_output"

    # Rule processing
    elif [[ "$line" =~ ^(HOST|HOST-SUFFIX|HOST-KEYWORD|IP-CIDR|IP6-CIDR) ]]; then
        # Convert rules to Surge/Loon format
        converted=$(echo "$line" | sed -E 's/HOST/DOMAIN/; s/HOST-SUFFIX/DOMAIN-SUFFIX/; s/HOST-KEYWORD/DOMAIN-KEYWORD/; s/IP6-CIDR/IP-CIDR6/')
        echo "$converted" >> "$surge_output"
        echo "$converted" >> "$loon_output"

    # MITM processing
    elif [[ "$line" =~ ^hostname ]]; then
        # Convert MITM to Surge and Loon formats
        surge_mitm=$(echo "$line" | sed 's/hostname = /Hostname = %APPEND% /')
        loon_mitm=$(echo "$line" | sed 's/hostname = /Hostname = /')
        echo "$surge_mitm" >> "$surge_output"
        echo "$loon_mitm" >> "$loon_output"

    # URL processing
    elif [[ "$line" =~ ^https?:\/\/raw\. ]]; then
        # Convert raw URLs to Surge/Loon format
        converted=$(echo "$line" | sed 's/raw\.githubusercontent\.com/github.com\/raw/')
        echo "$converted" >> "$surge_output"
        echo "$converted" >> "$loon_output"
    
    else
        # For any unrecognized line, keep it unchanged in both outputs
        echo "$line" >> "$surge_output"
        echo "$line" >> "$loon_output"
    fi

done < "$input_file"

echo "Conversion complete. Files generated:"
echo "Surge: $surge_output"
echo "Loon: $loon_output"
