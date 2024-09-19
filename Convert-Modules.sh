#!/bin/bash

# 检查是否传入了所有必要的参数
if [[ -z "$1" || -z "$2" ]]; then
  echo "Usage: $0 <input_file> <module_name> [comment]"
  exit 1
fi

# 传入的参数
input_file=$1  # 第一个参数：输入文件
module_name=$2  # 第二个参数：模块名称
comment=$3  # 第三个参数：注释（可选）

# 创建输出目录
mkdir -p Modules/Surge Modules/Loon

# 文件格式1转换函数
convert_format1() {
  while read -r line; do
    if [[ $line =~ ^(script-response-body|script-echo-response|script-response-header) ]]; then
      pattern=$(echo "$line" | awk '{print $1}')
      echo "$module_name = type=http-response,pattern=$pattern,requires-body=1,script-path=$(echo "$line" | awk '{print $4}')" >> Modules/Surge/${module_name}.sgmodule
      echo "http-response $pattern script-path=$(echo "$line" | awk '{print $4}'), requires-body=true, tag=${module_name}" >> Modules/Loon/${module_name}.plugin
    else
      pattern=$(echo "$line" | awk '{print $1}')
      echo "$module_name = type=http-request,pattern=$pattern,requires-body=0,script-path=$(echo "$line" | awk '{print $4}')" >> Modules/Surge/${module_name}.sgmodule
      echo "http-request $pattern script-path=$(echo "$line" | awk '{print $4}'), requires-body=false, tag=${module_name}" >> Modules/Loon/${module_name}.plugin
    fi
  done < "$input_file"
}

# 文件格式2转换函数
convert_format2() {
  while read -r line; do
    pattern=$(echo "$line" | awk '{print $1}')
    echo "$pattern - reject" >> Modules/Surge/${module_name}.sgmodule
    echo "$line" >> Modules/Loon/${module_name}.plugin
  done < "$input_file"
}

# 文件格式3转换函数
convert_format3() {
  while read -r line; do
    if [[ $line =~ ^HOST ]]; then
      echo "${line/HOST/DOMAIN}" >> Modules/Surge/${module_name}.sgmodule
      echo "${line/HOST/DOMAIN}" >> Modules/Loon/${module_name}.plugin
    elif [[ $line =~ ^IP-CIDR ]]; then
      echo "${line}, no-resolve" >> Modules/Surge/${module_name}.sgmodule
      echo "$line" >> Modules/Loon/${module_name}.plugin
    else
      echo "${line/;/#}" >> Modules/Surge/${module_name}.sgmodule
      echo "${line/;/#}" >> Modules/Loon/${module_name}.plugin
    fi
  done < "$input_file"
}

# 文件格式4转换函数
convert_format4() {
  while read -r line; do
    echo "${line/raw.githubusercontent.com/github.com}" >> Modules/Surge/${module_name}.sgmodule
    echo "${line/raw.githubusercontent.com/github.com}" >> Modules/Loon/${module_name}.plugin
  done < "$input_file"
}

# 文件格式5转换函数
convert_format5() {
  while read -r line; do
    echo "Hostname = %APPEND% $line" >> Modules/Surge/${module_name}.sgmodule
    echo "Hostname = $line" >> Modules/Loon/${module_name}.plugin
  done < "$input_file"
}

# 判断输入文件格式，并调用相应的转换函数
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
