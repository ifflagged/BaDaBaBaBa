#!/bin/bash

# Input file containing original lines (replace with your actual input file path)
input_file=$1

# Output directories for Surge and Loon
surge_output_dir="Modules/Surge"
loon_output_dir="Modules/Loon"

# Create the output directories if they don't exist
mkdir -p "$surge_output_dir"
mkdir -p "$loon_output_dir"

# Comment to add at the top of the files
comment=$3

# Common sed commands to be shared between Surge and Loon
sed_common="
    s/reject-200/- reject/Ig
    s/reject-img/- reject/Ig
    s/reject-dict/- reject/Ig
    s/reject-array/- reject/Ig
    s/reject-video/- reject/Ig
    s/reject-replace/- reject/Ig
    s/reject/- reject/Ig
"

# Loop through each line in the input file
while IFS= read -r line; do
  # Extract the tag value (e.g., RuCu6_amap)
  tag=$(echo "$line" | grep -oP '(?<=tag = ).*')

  # Derive module_name from the tag by removing any unwanted characters if necessary
  module_name="${tag// /_}"  # Replace spaces with underscores

  # SURGE conversion
  sed -e "1 i\\ $comment" \
      -e "$sed_common" \
      -e "s/url reject-200/- reject/Ig" \
      -e 's/url reject-img/- reject/Ig' \
      -e 's/url reject-dict/- reject/Ig' \
      -e 's/url reject-array/- reject/Ig' \
      -e 's/url reject-video/- reject/Ig' \
      -e 's/url reject-replace/- reject/Ig' \
      -e 's/url reject/- reject/Ig' \
      -e 's/, REJECT-DROP/, REJECT/Ig' \
      -e "/url script-response-body/ s/^/${module_name} = type=http-response,pattern=/" \
      -e "/url script-echo-response/ s/^/${module_name} = type=http-response,pattern=/" \
      -e "/url script-response-header/ s/^/${module_name} = type=http-response,pattern=/" \
      -e "/url script-request-body/ s/^/${module_name} = type=http-request,pattern=/" \
      -e "/url script-request-header/ s/^/${module_name} = type=http-request,pattern=/" \
      -e "/url script-analyze-echo-response/ s/^/${module_name} = type=http-request,pattern=/" \
      -e 's/ url script-response-body /,requires-body=1,script-path=/Ig' \
      -e 's/ url script-echo-response /,requires-body=1,script-path=/Ig' \
      -e 's/ url script-response-header /,requires-body=1,script-path=/Ig' \
      -e 's/ url script-request-body /,requires-body=1,script-path=/Ig' \
      -e 's/ url script-analyze-echo-response /,requires-body=1,script-path=/Ig' \
      -e 's/ url script-request-header /,requires-body=0,script-path=/Ig' \
      -e 's/hostname =/Hostname = %APPEND%/Ig' \
      "$input_file" > "${surge_output_dir}/${module_name}.sgmodule"

  # LOON conversion
  sed -e "1 i\\ $comment" \
      -e "$sed_common" \
      -e "s/url reject-200/reject-200/Ig" \
      -e 's/url reject-img/reject-img/Ig' \
      -e 's/url reject-dict/reject-dict/Ig' \
      -e 's/url reject-array/reject-array/Ig' \
      -e 's/url reject-video/reject-video/Ig' \
      -e 's/url reject-replace/reject-replace/Ig' \
      -e 's/url reject/reject/Ig' \
      -e "/url script-response-body/ s/^/http-response /" \
      -e "/url script-echo-response/ s/^/http-response /" \
      -e "/url script-response-header/ s/^/http-response /" \
      -e "/url script-request-body/ s/^/http-request /" \
      -e "/url script-request-header/ s/^/http-request /" \
      -e "/url script-analyze-echo-response/ s/^/http-request /" \
      -e "/script-response-body/ s/$/, requires-body = true, tag = ${module_name}/" \
      -e "/script-echo-response/ s/$/, requires-body = true, tag = ${module_name}/" \
      -e "/script-response-header/ s/$/, requires-body = true, tag = ${module_name}/" \
      -e "/script-request-body/ s/$/, requires-body = true, tag = ${module_name}/" \
      -e "/script-analyze-echo-response/ s/$/, requires-body = true, tag = ${module_name}/" \
      -e "/script-request-header/ s/$/, requires-body = false, tag = ${module_name}/" \
      -e 's/url script-response-body/script-path=/Ig' \
      -e 's/url script-echo-response/script-path=/Ig' \
      -e 's/url script-response-header/script-path=/Ig' \
      -e 's/url script-request-body/script-path=/Ig' \
      -e 's/url script-request-header/script-path=/Ig' \
      -e 's/url script-analyze-echo-response/script-path=/Ig' \
      -e 's/hostname =/Hostname =/Ig' \
      "$input_file" > "${loon_output_dir}/${module_name}.plugin"

done < "$input_file"

echo "Transformation complete. Results saved in $surge_output_dir and $loon_output_dir."
