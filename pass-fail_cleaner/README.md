# Test Result Cleaner

This script processes test result files and resolves PASS/FAIL conditions based on specified criteria.

## Overview

The script identifies lines ending with `PASS/FAIL` and determines the actual result by comparing the measured value against the expected criteria (marked with "S/B" = Should Be).

## Usage

### Single File

```bash
python test_result_cleaner.py <input_file> [output_file]
```

**Arguments:**
- `input_file` (required): Path to the test result file to process
- `output_file` (optional): Path where the processed file should be saved
  - If not specified, creates `<input_file>_cleaned.txt`

**Example:**
```bash
python test_result_cleaner.py test_results.txt
# Creates: test_results_cleaned.txt (only if PASS/FAIL conditions exist)

python test_result_cleaner.py input.txt output.txt
# Custom output filename
```

### Directory Processing

```bash
python test_result_cleaner.py <directory> [output_directory]
python test_result_cleaner.py -r <directory> [output_directory]
```

**Arguments:**
- `directory` (required): Path to directory containing log files
- `output_directory` (optional): Where to save processed files (defaults to same location)
- `-r` flag: Process subdirectories recursively

**Examples:**
```bash
# Process all files in a directory (non-recursive)
python test_result_cleaner.py /path/to/logs/
# Creates *_cleaned.txt files in /path/to/logs/ for each file with PASS/FAIL

# Process directory recursively
python test_result_cleaner.py -r /path/to/logs/
# Processes all files in /path/to/logs/ and subdirectories

# Specify output directory
python test_result_cleaner.py -r /path/to/logs/ /path/to/output/
# Preserves directory structure in output location
```

**Important:**
- Only files containing PASS/FAIL conditions are processed
- Files without PASS/FAIL conditions are skipped (no output file created)
- Output files are named `<original_name>_cleaned.<ext>`

## Supported Criteria Patterns

The script recognizes and handles various types of test criteria:

### 1. Exact Match
```
S/B VALUE
```
Example: `S/B NOWRAP` → Value must exactly match "NOWRAP"

### 2. Tolerance Range
```
S/B TARGET +/- TOLERANCE
```
Example: `S/B 27535 +/- 5` → Value must be between 27530 and 27540

### 3. Min-Max Range
```
S/B MIN to MAX
```
Example: `S/B 0 to 604799` → Value must be between 0 and 604799

### 4. Dash Range Format
```
S/B MIN - MAX
```
Example: `S/B 0 - 9999.9` → Value must be between 0 and 9999.9

### 5. Greater Than Comparison
```
S/B > THRESHOLD
```
Example: `S/B > 0` → Value must be greater than 0

### 6. Greater Than Previous
```
S/B Greater Than Previous MP XXX
S/B GREATER THAN PREVIOUS MP XXX
```
Example: `S/B Greater Than Previous MP 214` → Value must be greater than the previous occurrence of MP 214 in the file

**How it works:** The script maintains a dictionary of parameter names and their most recent values. When it encounters a "Greater Than Previous" criteria, it:
1. Looks up the previous value for that parameter
2. Compares current value > previous value
3. Stores the current value for future comparisons
4. First occurrence always passes (no previous value to compare)

### 7. Set of Allowed Values
```
S/B VALUE1 or VALUE2 or VALUE3
```
Example: `S/B 0 or 1 or blank` → Value must be 0, 1, or empty

### 8. Complex IP/Netmask Ranges
```
S/B in range of 0 to 255 and 0 to 255
S/B in range of 0 to 255 and 0 to 255 or DSABLD
```
Example: IP addresses formatted as two 3-character octets

**How it works:** The script:
1. Parses the value as two octets (e.g., "192168" → 192 and 168)
2. Handles variable widths: "1101" (4 chars), "192168" (6 chars), "255  0" (6 chars with spaces)
3. Tries multiple split points for ambiguous lengths
4. Validates each octet is 0-255
5. Accepts alternative values like "DSABLD" for disabled networks

### 9. Complex Patterns with "May be"
```
S/B X
X May be RANGE, VALUE1, VALUE2 or VALUE3
```
Example:
```
S/B X
X May be 1 - 9, A, B or C
```
This expands to: Value must be 1, 2, 3, 4, 5, 6, 7, 8, 9, A, B, or C

## How It Works

1. **Pattern Detection**: The script scans the file for lines ending with `PASS/FAIL`

2. **Criteria Extraction**: For each PASS/FAIL line, it looks backwards (up to 10 lines) to find the criteria line starting with "S/B"

3. **Multi-line Criteria**: If the criteria is just a placeholder (like "X" or "XX"), the script checks the next line for additional information (e.g., "X May be...")

4. **Value Extraction**: Extracts the measured value from the test line (typically after an `=` sign)

5. **Comparison**: Compares the measured value against the parsed criteria

6. **Result**: Replaces `PASS/FAIL` with either `PASS` or `FAIL` based on the comparison

## Output

The script outputs a processed file that is identical to the input, except all `PASS/FAIL` instances are replaced with the determined result.

### Statistics

After processing, the script displays:
- Total number of PASS/FAIL instances found
- How many were resolved as PASS
- How many were resolved as FAIL
- How many were left unchanged (if criteria couldn't be determined)

Example output:
```
Processing: test_results.txt
Output to: test_results_cleaned.txt
------------------------------------------------------------

Processing complete!
Total PASS/FAIL instances found: 90
  - Resolved as PASS: 66
  - Resolved as FAIL: 24
  - Left unchanged: 0

Output written to: test_results_cleaned.txt
```

## Technical Details

### Value Comparison

- **String values**: Case-insensitive comparison
- **Numeric values**: Parsed as floats for tolerance and range comparisons
- **Hex values**: Automatically detected and compared in hexadecimal
- **Empty values**: Pass if "blank" is in the allowed set of values

### Range Expansion

When a range like "1 - 9" is specified in a "May be" pattern, the script:
1. Detects the numeric range using regex
2. Expands it to individual values: [1, 2, 3, 4, 5, 6, 7, 8, 9]
3. Combines with other allowed values in the same criterion

### Error Handling

- If the input file doesn't exist, an error is raised
- If criteria cannot be determined, the PASS/FAIL is left unchanged
- If a value cannot be extracted, the PASS/FAIL is left unchanged
- All file encoding issues are handled gracefully

## Limitations

- The script looks backwards up to 10 lines for criteria
- Criteria must be marked with "S/B" (case-insensitive)
- Values are extracted from patterns containing `=`
- Complex nested conditions are not supported

## Requirements

- Python 3.6 or higher
- No external dependencies (uses only standard library)
