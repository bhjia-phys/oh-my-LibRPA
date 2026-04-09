import re
import sys

def find_min_free_memory(filename):
    # 修正后的正则表达式，匹配 "Free memory on node [GB]: <number>"
    pattern = re.compile(r'Free memory on node \[GB\]:\s*(\d+\.\d+)')
    numbers = []

    with open(filename, 'r') as file:
        for line_num, line in enumerate(file, 1):
            match = pattern.search(line)
            if match:
                try:
                    number = float(match.group(1))
                    numbers.append(number)
                    # 调试信息：显示匹配成功的行
                    #print(f"Line {line_num}: Matched value = {number}")
                except ValueError:
                    print(f"Line {line_num}: Invalid number format: {match.group(1)}")

    if numbers:
        min_memory = min(numbers)
        print(f"Minimum free memory: {min_memory:.3f} GB")
    else:
        print("Error: No memory values detected. Possible causes:")
        print("1. Log format mismatch (check timestamp prefixes)")
        print("2. File contains non-standard decimal separators")
        print("3. Memory entries use unexpected formatting")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python get_min_memory.py <logfile>")
        sys.exit(1)
    find_min_free_memory(sys.argv[1])