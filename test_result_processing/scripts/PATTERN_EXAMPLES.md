# Pattern Examples - Pass-Fail Cleaner

This document shows all the test criteria patterns that the Pass-Fail Cleaner can recognize and validate.

## Table of Contents

1. [Exact Match](#1-exact-match)
2. [Tolerance (±)](#2-tolerance-)
3. [Numeric Range](#3-numeric-range)
4. [Value Set (OR)](#4-value-set-or)
5. [Greater Than (>)](#5-greater-than-)
6. [Greater Than Previous](#6-greater-than-previous)
7. [Cross-Reference](#7-cross-reference)
8. [Complex Range (IP/Netmask)](#8-complex-range-ipnetmask)
9. ["May Be" Patterns](#9-may-be-patterns)
10. [Standalone PASS/FAIL](#10-standalone-passfail)
11. [Encoding Handling](#11-encoding-handling)

---

## 1. Exact Match

### Pattern
```
S/B <exact_value>
```

### How It Works
The measured value must exactly match the expected value (case-insensitive).

### Examples

**Test File:**
```
MP 1 S/B 100
MP 1 = 100  PASS/FAIL
```
**Result:** PASS (100 == 100)

---

**Test File:**
```
MP 2 S/B DISABLED
MP 2 = DISABLED  PASS/FAIL
```
**Result:** PASS (case-insensitive match)

---

**Test File:**
```
MP 3 S/B 5A3F
MP 3 = 5A3F  PASS/FAIL
```
**Result:** PASS (exact hex match)

---

## 2. Tolerance (±)

### Pattern
```
S/B <value> +/- <tolerance>
S/B <value> ± <tolerance>
```

### How It Works
The measured value must be within the tolerance range of the target value.  
Accepts values with units (Deg, Hz, etc.) - units are stripped for comparison.

### Examples

**Test File:**
```
ST6.17 S/B 0.000000 +/- 180.000000 Deg
ST6.17 = 136.974944 Deg			PASS/FAIL
```
**Result:** PASS (136.974944 is within 0 ± 180)

---

**Test File:**
```
Frequency S/B 1000 +/- 10 Hz
Frequency = 1005 Hz  PASS/FAIL
```
**Result:** PASS (1005 is within 1000 ± 10)

---

**Test File:**
```
Voltage S/B 5.0 +/- 0.1
Voltage = 5.2  PASS/FAIL
```
**Result:** FAIL (5.2 is outside 5.0 ± 0.1)

---

## 3. Numeric Range

### Pattern
```
S/B <min> to <max>
S/B <min> - <max>
```

### How It Works
The measured value must fall within the specified range (inclusive).  
Supports numeric, hexadecimal, and alphabetic ranges.

### Examples

**Numeric Range:**
```
MP 10 S/B 0 to 604799
MP 10 = 123456  PASS/FAIL
```
**Result:** PASS (123456 is between 0 and 604799)

---

**Hex Range:**
```
MP 20 S/B 0000 to FFFF
MP 20 = A5B3  PASS/FAIL
```
**Result:** PASS (A5B3 is between 0000 and FFFF in hex)

---

**Hyphen Format:**
```
MP 30 S/B 0 - 9999.9
MP 30 = 5432.1  PASS/FAIL
```
**Result:** PASS (5432.1 is between 0 and 9999.9)

---

## 4. Value Set (OR)

### Pattern
```
S/B <value1> or <value2> or <value3>
S/B <value1>, <value2>, <value3>
```

### How It Works
The measured value must match one of the allowed values (case-insensitive).  
Supports "blank" as a valid value.

### Examples

**Simple OR:**
```
MP 40 S/B 0 or 1
MP 40 = 1  PASS/FAIL
```
**Result:** PASS (1 is in the set {0, 1})

---

**Multiple Values:**
```
MP 50 S/B A or B or C
MP 50 = B  PASS/FAIL
```
**Result:** PASS (B is in the set {A, B, C})

---

**Including Blank:**
```
MP 60 S/B 0 or 9 or blank
MP 60 =   PASS/FAIL
```
**Result:** PASS (blank/empty value is allowed)

---

## 5. Greater Than (>)

### Pattern
```
S/B > <threshold>
```

### How It Works
The measured value must be strictly greater than the threshold.

### Examples

**Test File:**
```
MP 70 S/B > 1000
MP 70 = 1500  PASS/FAIL
```
**Result:** PASS (1500 > 1000)

---

**Test File:**
```
MP 71 S/B > 100.5
MP 71 = 99.9  PASS/FAIL
```
**Result:** FAIL (99.9 is not > 100.5)

---

## 6. Greater Than Previous

### Pattern
```
S/B Greater Than Previous <param_name>
```

### How It Works
Compares current value to the previous occurrence of the same parameter.  
First occurrence always passes (no previous value to compare).

### Examples

**Test File:**
```
MP 214 S/B Greater Than Previous MP 214
MP 214 = 100  PASS/FAIL

MP 214 S/B Greater Than Previous MP 214
MP 214 = 150  PASS/FAIL

MP 214 S/B Greater Than Previous MP 214
MP 214 = 120  PASS/FAIL
```
**Results:**
- Line 1: PASS (first occurrence, no previous value)
- Line 2: PASS (150 > 100)
- Line 3: FAIL (120 is not > 150)

---

## 7. Cross-Reference

### Pattern
```
S/B = <REFERENCE_PARAM>
```

### How It Works
The measured value should match the value of another parameter elsewhere in the file.  
Searches backwards up to 20 lines to find the reference value.  
Handles hex values with leading zeros (e.g., "00629" matches "629").

### Examples

**Test File:**
```
VEN2.01/02 = 50303031

MP 285 S/B = VEN2.01/02
MP 285 = 5030 3031  PASS/FAIL
```
**Result:** PASS (normalized values match: 50303031 == 50303031)

---

**Hex with Leading Zeros:**
```
VEN2.22 = 3d

MP 503 S/B = VEN2.22
MP 503 = 003D  PASS/FAIL
```
**Result:** PASS (hex comparison: 0x3d == 0x003d)

---

**Direct Value (Not a Reference):**
```
MP 100 S/B = 30000
MP 100 = 30000  PASS/FAIL
```
**Result:** PASS (direct numeric comparison)

---

## 8. Complex Range (IP/Netmask)

### Pattern
```
S/B in range of X to Y and X to Y
S/B in range of X to Y and X to Y or DSABLD
```

### How It Works
Validates IP address octets or netmask values.  
Handles compact formats like "192168" (two 3-digit octets).  
Supports alternative values like "DSABLD".

### Examples

**IP Address Validation:**
```
MP 301 S/B in range of 1 to 239 and 1 to 255
MP 301 = 192168  PASS/FAIL
```
**Result:** PASS (192 is 1-239, 168 is 1-255)

---

**With Alternative:**
```
MP 302 S/B in range of 1 to 239 and 1 to 255 or DSABLD
MP 302 = DSABLD  PASS/FAIL
```
**Result:** PASS (matches alternative value)

---

## 9. "May Be" Patterns

### Pattern
```
S/B May be <value1> or <value2>
S/B May be <range> or <values>
S/B May be <min> to <max>
```

### How It Works
Flexible validation supporting ranges, sets, or combinations.  
Can mix numeric ranges with individual values.

### Examples

**Simple Set:**
```
MP 90 S/B May be 0 or 1
MP 90 = 0  PASS/FAIL
```
**Result:** PASS (0 is in the set)

---

**Range:**
```
MP 91 S/B May be 0 to 9
MP 91 = 5  PASS/FAIL
```
**Result:** PASS (5 is in range 0-9)

---

**Mixed Format:**
```
MP 92 S/B May be 1 - 9, A, B or C
MP 92 = 7  PASS/FAIL
```
**Result:** PASS (7 is in range 1-9)

---

**Alternative Test:**
```
MP 93 S/B May be 1 - 9, A, B or C
MP 93 = A  PASS/FAIL
```
**Result:** PASS (A is in the value set)

---

## 10. Standalone PASS/FAIL

### Pattern
PASS/FAIL appears on its own line (with only whitespace), separate from the value line.

### How It Works
Script looks backward (up to 3 lines) to find the value line with "=".  
Then looks further back for the "S/B" criteria line.

### Examples

**Standalone on Next Line:**
```
ST6A.23 S/B 0.000000 +/- 180.000000 Deg
ST6A.23 = 45.635844 Deg
			PASS/FAIL**
```
**Result:** PASS (45.635844 is within 0 ± 180)

---

**Multiple Instances:**
```
EST6A.35 S/B 0.000000 +/- 180.000000 Deg
EST6A.35 = 10.524588 Deg
			PASS/FAIL**

ST6A.25 S/B 0.000000 +/- 180.000000 Deg
ST6A.25 = 10.519095 Deg			PASS/FAIL
```
**Results:** Both PASS (tolerance validation works for both formats)

---

## 11. Encoding Handling

### Special Characters Support

The script handles files with special characters using encoding fallback:

**Windows-1252 Characters:**
```
ECEF Position – Xe        (en-dash: –)
DPRAM STATUS WORD ½       (half symbol: ½)
```
**Result:** Characters preserved in output

---

**Undefined Bytes:**
Files with undefined Windows-1252 bytes (0x81, 0x8D, 0x8F, 0x90, 0x9D) automatically fall back to Latin-1 encoding with error replacement.

**Result:** File processed without errors

---

## Pattern Detection Priority

The script checks patterns in this order:

1. **Cross-reference** (`= REFERENCE`)
2. **Complex range** (`in range of`)
3. **Numeric range** (`to` or `-`)
4. **Greater than previous**
5. **Greater than** (`>`)
6. **Tolerance** (`+/-` or `±`)
7. **"May be" patterns**
8. **Value set** (`or`)
9. **Exact match** (default)

---

## Variations Handled

### PASS/FAIL Formats
- `PASS/FAIL` (standard)
- `PASS/FAIL**` (with trailing asterisks)
- `PASS/FAIL   ` (with trailing spaces)
- Standalone PASS/FAIL on separate line

### Value Formats
- With units: `136.974944 Deg`
- Hex values: `5A3F`, `00A5`
- With spaces: `5030 3031`
- With colons: `10EC:9EFB`
- Empty/blank values

### Criteria Formats
- Case-insensitive matching
- Multiple spaces handled
- Various separators (`:`, `=`, spaces)

---

## Output

### Resolved Results
```
MP 1 = 100  PASS
MP 2 = 50   FAIL
```

### Line Number Breadcrumbs
When processing, failed and unchanged instances show line numbers:
```
✓ 12 instances: 11 PASS, 1 FAIL, 0 unchanged
  FAIL at lines: 1177
```

---

## Summary Statistics

After processing, you'll see:
```
Total PASS/FAIL instances: 344
  - Resolved as PASS: 343
  - Resolved as FAIL: 1
    Line numbers: 1177
  - Left unchanged: 0
```

**Unchanged** means the script couldn't automatically validate (e.g., unknown pattern or missing criteria).

---

## File Naming

Processed files are saved with `_processed` suffix:
- **Input:** `A0807XMP_SFF.TXT`
- **Output:** `A0807XMP_SFF_processed.TXT`

Original files are never modified.
