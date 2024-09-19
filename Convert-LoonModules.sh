#!/bin/bash

# Input file containing original lines (replace with your actual input file path)
input_file="input.txt"

# Directory to save the output files
output_dir="Modules/Surge"

# Create the output directory if it doesn't exist
mkdir -p "$output_dir"

# Loop through each line in the input file
while IFS= read -r line; do
  # Extract the tag value (e.g., RuCu6_amap)
  tag=$(echo "$line" | grep -oP '(?<=tag = ).*')

  # Extract whether it's http-response or http-request
  type=$(echo "$line" | grep -oP '^(http-\w+)')

  # Extract the pattern (e.g., ^http:\/\/amdc\.m\.taobao\.com\/amdc\/mobileDispatch)
  pattern=$(echo "$line" | grep -oP '(?<=(http-response|http-request) ).*(?= script-path)')

  # Extract the script-path URL (e.g., https://github.com/RuCu6/QuanX/raw/main/Scripts/header.js)
  script_path=$(echo "$line" | grep -oP '(?<=script-path= ).*(?=, requires-body)')

  # Determine if requires-body is true or false and convert it to 0/1
  requires_body=$(echo "$line" | grep -oP '(?<=requires-body = ).*')
  if [ "$requires_body" = "true" ]; then
    requires_body=1
  else
    requires_body=0
  fi

  # Derive module_name from the tag by removing any unwanted characters if necessary
  module_name="${tag// /_}"  # Replace spaces with underscores

  # Format the output string in the desired format
  if [ -n "$tag" ] && [ -n "$pattern" ] && [ -n "$script_path" ] && [ -n "$type" ]; then
    output_file="$output_dir/${module_name}.sgmodule"
    echo "$tag = type=$type,pattern=$pattern,requires-body=$requires_body,script-path=$script_path" >> "$output_file"
  fi
done < "$input_file"

# Apply the existing replacement rules to all the generated files
find "$output_dir" -type f -name "*.sgmodule" -exec sed -i \
    -e "s/reject-200/- reject/Ig" \
    -e 's/reject-img/- reject/Ig' \
    -e 's/reject-dict/- reject/Ig' \
    -e 's/reject-array/- reject/Ig' \
    -e 's/reject-video/- reject/Ig' \
    -e 's/reject-replace/- reject/Ig' \
    -e 's/reject/- reject/Ig' \
    {} +

echo "Transformation complete. Results saved in the $output_dir directory."
