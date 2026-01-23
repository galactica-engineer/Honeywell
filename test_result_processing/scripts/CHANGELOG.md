# Pass-Fail Cleaner - Changelog

## Version 3 (Current)

### New Features

**Directory Processing**
- Added ability to process entire directories of log files
- Recursive mode (`-r` flag) to process subdirectories
- Smart filtering: Only processes files that contain PASS/FAIL conditions
- Files without PASS/FAIL conditions are automatically skipped (no output file created)
- Preserves directory structure when using output directory option
- Summary statistics for batch processing

**Usage:**
```bash
# Single directory (non-recursive)
python test_result_cleaner.py /path/to/logs/

# Recursive processing
python test_result_cleaner.py -r /path/to/logs/

# With output directory
python test_result_cleaner.py -r /path/to/logs/ /path/to/output/
```

---

## Version 2

### Overview

Version 2 of the Pass-Fail Cleaner addresses all the false failures identified in the initial version. All 90 test instances now resolve correctly.

## Results Comparison

| Metric | Version 1 | Version 2 |
|--------|-----------|-----------|
| Total Instances | 90 | 90 |
| Resolved as PASS | 66 | 90 |
| Resolved as FAIL | 24 | 0 |
| Left Unchanged | 0 | 0 |
| Accuracy | 73% | 100% |

## Issues Fixed

### 1. Blank/Empty Values Not Recognized
**Problem:** Values that were blank (only whitespace) were not being properly detected when criteria included "or blank"

**Examples:**
- MP 531: `S/B 0 or 9 or blank` with empty value → Was incorrectly marked FAIL
- MP 532: `S/B 0 or 9 or blank` with empty value → Was incorrectly marked FAIL

**Fix:** 
- Updated value extraction to use `.*` instead of `.+` to allow empty captures
- Improved empty value detection to check `value.strip() == ''`
- Fixed "blank" matching in set comparison to be case-insensitive

---

### 2. "Greater Than" Comparisons Not Supported
**Problem:** The `>` operator was not being parsed

**Examples:**
- MP 34: `S/B > 0` with value 4 → Was incorrectly marked FAIL

**Fix:** Added dedicated handler for `>` operator that extracts threshold and performs numeric comparison

---

### 3. "Greater Than Previous" Pattern Not Recognized
**Problem:** Comparisons requiring state tracking (comparing to previous values) were not handled

**Examples:**
- MP 214: `S/B Greater Than Previous MP 214` → Was incorrectly marked FAIL
- MP 215: `S/B Greater Than Previous MP 215` → Was incorrectly marked FAIL
- MP 34: `S/B GREATER THAN PREVIOUS MP 34` → Was incorrectly marked FAIL
- MP 113: `S/B GREATER THAN PREVIOUS MP 113` → Was incorrectly marked FAIL

**Fix:** Implemented proper state tracking with a `previous_values` dictionary that:
1. Stores each parameter's value as it's processed
2. Extracts the parameter name from "Greater Than Previous MP XXX" criteria
3. Compares current value against stored previous value
4. Returns True for first occurrence (no previous value)
5. Returns True/False based on current > previous for subsequent occurrences

---

### 4. Dash Range Format Not Supported
**Problem:** Ranges using dash format (e.g., "0 - 9999.9") were not being parsed

**Examples:**
- MP 113: `S/B 0 - 9999.9` with value 6.5 → Was incorrectly marked FAIL

**Fix:** Added regex pattern to recognize numeric ranges in "MIN - MAX" format (distinct from "MIN to MAX")

---

### 5. Complex IP/Netmask Ranges Not Properly Validated
**Problem:** The "in range of X to Y and X to Y" pattern was accepting any value without validation

**Examples:**
- MP 400: `S/B in range of 0 to 255 and 0 to 255` with value 192168 → Was incorrectly marked FAIL (then incorrectly always PASS)
- MP 401: `S/B in range of 0 to 255 and 0 to 255` with value 1101 → Was incorrectly marked FAIL (then incorrectly always PASS)
- MP 402: `S/B in range of 0 to 255 and 0 to 255` with value 255255 → Was incorrectly marked FAIL (then incorrectly always PASS)
- MP 403: `S/B in range of 0 to 255 and 0 to 255` with value "255  0" → Was incorrectly marked FAIL (then incorrectly always PASS)

**Fix:** Implemented proper dual-octet validation that:
1. Parses values as two octets (e.g., "192168" = octets 192 and 168)
2. Handles variable-width formats (4-6 characters)
3. Validates each octet is in range 0-255
4. Tries multiple split points for ambiguous values (e.g., "1101" could be "1,101" or "11,01" or "110,1")
5. Accepts only splits where both octets are valid 0-255

**Test cases:**
- "192168" = 192, 168 → PASS ✓
- "1101" = 1, 101 → PASS ✓  
- "256100" = 256, 100 → FAIL (256 > 255) ✓
- "100300" = 100, 300 → FAIL (300 > 255) ✓
- "DSABLD" → PASS (alternative value) ✓

---

### 6. Alternative Values in Complex Patterns Not Recognized
**Problem:** The "or DSABLD" alternative in complex range patterns was not being detected

**Examples:**
- MP 404-415: `S/B in range of 0 to 255 and 0 to 255 or DSABLD` with value "DSABLD" → Were incorrectly marked FAIL

**Fix:** 
- Reordered pattern matching so "in range of" is checked before generic "to" patterns
- Added extraction of alternative values from "or ALTERNATIVE" at end of criteria
- Updated complex_range type to check for alternative value matches

---

### 7. Pattern Matching Order Issues
**Problem:** Some patterns were being matched by more generic patterns before reaching their specific handlers

**Examples:**
- Criteria with "May be" were being caught by the "or" pattern first
- Criteria with "in range of" were being caught by the "to" pattern first

**Fix:** Reordered pattern matching to check more specific patterns before generic ones:
1. "in range of" (complex patterns)
2. "may be" (complex range expansion)  
3. "to" (simple ranges)
4. "or" (simple sets)

---

## New Patterns Supported

Version 2 adds support for these additional pattern types:

1. **Greater Than (`>`)**: `S/B > THRESHOLD`
2. **Greater Than Previous**: `S/B Greater Than Previous MP XXX`
3. **Dash Range**: `S/B MIN - MAX`
4. **Complex IP/Netmask**: `S/B in range of X to Y and X to Y`
5. **Complex with Alternative**: `S/B in range of X to Y and X to Y or VALUE`

---

## Technical Improvements

### State Tracking
- Added `previous_values` dictionary to store parameter values
- Automatically extracts parameter names (e.g., "MP 214") from lines
- Stores numeric values as floats for accurate comparison
- Maintains state throughout file processing

### Value Extraction
- Changed from `=\s*([^\t]+)` to `=\s*(.*)$` with PASS/FAIL removal
- Now correctly handles empty values and preserves spacing
- Added `extract_param_name()` method to identify parameters

### Empty Value Handling
- Improved detection: `not value or value.strip() == ''`
- Case-insensitive "blank" matching in criteria

### Pattern Priority
- Specific patterns checked before generic ones
- Prevents misclassification of complex criteria

### New Criteria Types
- `greater_than_previous`: Compares against stored previous value
- `complex_range`: For IP/netmask validation with alternatives
- `greater_than`: For threshold comparisons
- `unvalidatable`: For patterns that truly can't be validated

---

## Validation

All 24 previously failing instances now correctly resolve as PASS:
- 2 blank value cases (MP 531, 532)
- 4 "greater than previous" cases (MP 214, 215, 34, 113)
- 2 ">" operator cases (MP 34)
- 2 "dash range" cases (MP 113)
- 14 complex IP/netmask cases (MP 400-415)

**Result: 100% accuracy on all 90 test instances**
