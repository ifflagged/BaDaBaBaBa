#!/bin/bash

# 检查是否传入了所有必要的参数
if [[ -z "$1" || -z "$2" ]]; then
  echo "Usage: $0 <input_file> <module_name> [comment]"
  exit 1
fi

# 参数传入
input_file=$1  # 输入文件路径
module_name=$2  # 模块名称
comment=$3  # 可选注释

# 创建输出目录
mkdir -p Modules/Surge Modules/Loon

# 格式1处理函数
convert_format1() {
  while read -r line; do
    if [[ $line =~ ^(http|https) ]]; then
      url=$(echo "$line" | awk '{print $1}')
      action=$(echo "$line" | awk '{print $3}')
      script=$(echo "$line" | awk '{print $4}')

      # 根据不同的 action 来区分是否是 http-response 或 http-request
      if [[ $action =~ ^(script-response-body|script-echo-response|script-response-header)$ ]]; then
        echo "$module_name = type=http-response,pattern=$url,requires-body=1,script-path=$script" >> Modules/Surge/${module_name}.sgmodule
        echo "http-response $url script-path=$script, requires-body=true, tag=${module_name}" >> Modules/Loon/${module_name}.plugin
      else
        echo "$module_name = type=http-request,pattern=$url,requires-body=0,script-path=$script" >> Modules/Surge/${module_name}.sgmodule
        echo "http-request $url script-path=$script, requires-body=false, tag=${module_name}" >> Modules/Loon/${module_name}.plugin
      fi
    fi
  done < "$input_file"
}

# 格式2处理函数
convert_format2() {
  while read -r line; do
    url=$(echo "$line" | awk '{print $1}')
    echo "$url - reject" >> Modules/Surge/${module_name}.sgmodule
    echo "$line" >> Modules/Loon/${module_name}.plugin
  done < "$input_file"
}

# 格式3处理函数
convert_format3() {
  while read -r line; do
    if [[ $line =~ ^HOST ]]; then
      echo "${line/HOST/DOMAIN}" >> Modules/Surge/${module_name}.sgmodule
      echo "${line/HOST/DOMAIN}" >> Modules/Loon/${module_name}.plugin
    elif [[ $line =~ ^IP-CIDR ]]; then
      echo "$line, no-resolve" >> Modules/Surge/${module_name}.sgmodule
      echo "$line" >> Modules/Loon/${module_name}.plugin
    else
      echo "${line/;/#}" >> Modules/Surge/${module_name}.sgmodule
      echo "${line/;/#}" >> Modules/Loon/${module_name}.plugin
    fi
  done < "$input_file"
}

# 格式4处理函数
convert_format4() {
  while read -r line; do
    echo "${line/raw.githubusercontent.com/github.com}" >> Modules/Surge/${module_name}.sgmodule
    echo "${line/raw.githubusercontent.com/github.com}" >> Modules/Loon/${module_name}.plugin
  done < "$input_file"
}

# 格式5处理函数
convert_format5() {
  while read -r line; do
    echo "Hostname = %APPEND% $line" >> Modules/Surge/${module_name}.sgmodule
    echo "Hostname = $line" >> Modules/Loon/${module_name}.plugin
  done < "$input_file"
}

# 根据输入文件格式选择相应的转换函数
if grep -q "^http" "$input_file"; then
  convert_format1
elif grep -q "url reject" "$input_file"; then
  convert_format2
elif grep -q "HOST" "$input_file"; then
  convert_format3
elif grep -q "raw.githubusercontent.com" "$input_file"; then
  convert_format4
elif grep -q "hostname =" "$input_file"; then
  convert_format5
else
  echo "Unknown file format. Please check the input file."
  exit 1
fi

# 添加注释（如果提供了注释）
if [[ -n "$comment" ]]; then
  echo "# $comment" >> Modules/Surge/${module_name}.sgmodule
  echo "# $comment" >> Modules/Loon/${module_name}.plugin
fi

echo "转换完成，结果已保存到 Modules/Surge/${module_name}.sgmodule 和 Modules/Loon/${module_name}.plugin"
