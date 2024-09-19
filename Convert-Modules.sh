#!/bin/bash

# Input parameters
input_file=$1
module_name=$2
comment=$3

# Output paths
surge_output="Modules/Surge/${module_name}.sgmodule"
loon_output="Modules/Loon/${module_name}.plugin"

# Create directories if they don't exist
mkdir -p "$(dirname "$surge_output")"
mkdir -p "$(dirname "$loon_output")"

# Initialize the output files
echo "# Surge module: $module_name" > "$surge_output"
echo "# Loon plugin: $module_name" > "$loon_output"

# Processing function for each line of input
process_line() {
  local line="$1"
  local surge_result=""
  local loon_result=""

  # Script-Type URL pattern handling
  if [[ $line =~ $Script_Type ]]; then
    script_url="${BASH_REMATCH[3]}"
    if [[ ${BASH_REMATCH[2]} =~ (script-response-body|script-echo-response|script-response-header|script-analyze-echo-response) ]]; then
      requires_body="1"
      surge_type="http-response"
    else
      requires_body="0"
      surge_type="http-request"
    fi
    # Surge format
    surge_result="${module_name} = type=${surge_type},pattern=${BASH_REMATCH[1]},requires-body=${requires_body},script-path=${script_url}"
    # Loon format
    loon_result="${surge_type} ${BASH_REMATCH[1]} script-path=${script_url}, requires-body=${requires_body}, tag=${module_name}"

  # URL Rewrite handling
  elif [[ $line =~ $URL_Rewrite ]]; then
    # Surge format
    surge_result="${BASH_REMATCH[1]} - ${BASH_REMATCH[2]}"
    # Loon format
    loon_result="${BASH_REMATCH[1]} ${BASH_REMATCH[2]}"

  # URL conversion handling
  elif [[ $line =~ https://raw\.githubusercontent\.com ]]; then
    # Surge & Loon both have the same URL conversion
    surge_result=$(echo "$line" | sed -e 's/raw.githubusercontent.com/github.com/' -e 's/\/main\//\/raw\/main\//' -e 's/\/master\//\/raw\/master\//')
    loon_result="$surge_result"

  # MITM (hostname) handling
  elif [[ $line =~ hostname ]]; then
    # Surge format
    surge_result="Hostname = %APPEND% ${line#*=}"
    # Loon format
    loon_result="Hostname = ${line#*=}"

  # Rule conversion (Rule file format)
  elif [[ $line =~ ^HOST ]]; then
    # Surge format
    surge_result=$(echo "$line" | sed 's/HOST/DOMAIN/' | sed 's/REJECT/& no-resolve/')
    loon_result=$(echo "$line" | sed 's/HOST/DOMAIN/')
  fi

  # Write to output files
  if [[ -n $surge_result ]]; then
    echo "$surge_result" >> "$surge_output"
  fi
  if [[ -n $loon_result ]]; then
    echo "$loon_result" >> "$loon_output"
  fi
}

# Read and process the input file line by line
while IFS= read -r line; do
  process_line "$line"
done < "$input_file"

echo "Conversion complete. Output files generated:"
echo "$surge_output"
echo "$loon_output"
