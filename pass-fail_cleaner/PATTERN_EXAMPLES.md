# Test Result Cleaner - Pattern Examples

This document shows examples of the different pass/fail patterns that the script can detect and resolve.

## Pattern 1: Simple Comparison (Actual = Expected)

**Input:**
```
G-1.02 BIT 03 S/B 1 
G-1.02 BIT 03 = 1 				PASS/FAIL
```

**Output:**
```
G-1.02 BIT 03 S/B 1 
G-1.02 BIT 03 = 1 				PASS
```

**Logic:** Value "1" equals expected "1" → **PASS**

---

## Pattern 2: Tolerance Range (Target +/- Tolerance)

**Input:**
```
=====MP 202 (GPS LATITUDE)===== 
MP 202 S/B 27535 +/- 5. 
MP 202 =  27535				PASS/FAIL
```

**Output:**
```
=====MP 202 (GPS LATITUDE)===== 
MP 202 S/B 27535 +/- 5. 
MP 202 =  27535				PASS
```

**Logic:** Value 27535 is within [27530, 27540] → **PASS**

---

## Pattern 3: Min-Max Range (X to Y)

**Input:**
```
=====MP 214 (GPS TIME OF WEEK)===== 
MP 214 S/B 0 to 604799. 
MP 214 = 425765				PASS/FAIL
```

**Output:**
```
=====MP 214 (GPS TIME OF WEEK)===== 
MP 214 S/B 0 to 604799. 
MP 214 = 425765				PASS
```

**Logic:** Value 425765 is within range [0, 604799] → **PASS**

---

## Pattern 4: Set of Allowed Values (X or Y or Z)

**Input:**
```
=====MP 530 (ARINC RX Chanels)===== 
MP 530 S/B 0 or 1
MP 530 =      0				PASS/FAIL
```

**Output:**
```
=====MP 530 (ARINC RX Chanels)===== 
MP 530 S/B 0 or 1
MP 530 =      0				PASS
```

**Logic:** Value "0" is in the set {0, 1} → **PASS**

---

## Pattern 5: Multi-line Criteria with Range Expansion

**Input:**
```
MP 200 S/B X 
X May be 1 - 9, A, B or C 
MP 200 =      A				PASS/FAIL
```

**Output:**
```
MP 200 S/B X 
X May be 1 - 9, A, B or C 
MP 200 =      A				PASS
```

**Logic:** 
1. Range "1 - 9" expands to {1, 2, 3, 4, 5, 6, 7, 8, 9}
2. Combined with {A, B, C}
3. Final set: {1, 2, 3, 4, 5, 6, 7, 8, 9, A, B, C}
4. Value "A" is in this set → **PASS**

---

## Pattern 6: Numeric Range with Multiple Options

**Input:**
```
MP 208 S/B XX. 
XX May be 00 to 79
MP 208 =     47				PASS/FAIL
```

**Output:**
```
MP 208 S/B XX. 
XX May be 00 to 79
MP 208 =     47				PASS
```

**Logic:** Value 47 is within range [0, 79] → **PASS**

---

## Pattern 7: Including "blank" as Valid Value

**Input:**
```
=====MP 531 (ARINC RX Chanel 1 Label 271)===== 
MP 531 S/B 0 or 9 or blank 
MP 531 =       				PASS/FAIL
```

**Output:**
```
=====MP 531 (ARINC RX Chanel 1 Label 271)===== 
MP 531 S/B 0 or 9 or blank 
MP 531 =       				PASS
```

**Logic:** Value is empty/blank, and "blank" is in the allowed set → **PASS**

---

## Pattern 8: Hexadecimal Range

**Input:**
```
=====MP 540 (DISCRETES)===== 
MP 540 S/B 0000 to FFFF
MP 540 =   030F				PASS/FAIL
```

**Output:**
```
=====MP 540 (DISCRETES)===== 
MP 540 S/B 0000 to FFFF
MP 540 =   030F				PASS
```

**Logic:** Hex value 030F (783 decimal) is within hex range [0000, FFFF] → **PASS**

---

## Pattern 9: String Match

**Input:**
```
=====MP 551 (RS422 Wraparound Results)===== 
MP 551 S/B NOWRAP 
MP 551 = NOWRAP				PASS/FAIL
```

**Output:**
```
=====MP 551 (RS422 Wraparound Results)===== 
MP 551 S/B NOWRAP 
MP 551 = NOWRAP				PASS
```

**Logic:** Value "NOWRAP" exactly matches expected "NOWRAP" (case-insensitive) → **PASS**

---

## Pattern 10: Binary Format Range

**Input:**
```
=====MP 550 (RS422 Wraparound)===== 
MP 550 S/B 000 to 111 (binary format) 
MP 550 =    000				PASS/FAIL
```

**Output:**
```
=====MP 550 (RS422 Wraparound)===== 
MP 550 S/B 000 to 111 (binary format) 
MP 550 =    000				PASS
```

**Logic:** Value "000" is within string range ["000", "111"] → **PASS**

---

## Failure Example

**Input:**
```
=====MP 203 (GPS LONGITUDE)===== 
MP 203 S/B - 82435 +/- 5. 
MP 203 = - 82450				PASS/FAIL
```

**Output:**
```
=====MP 203 (GPS LONGITUDE)===== 
MP 203 S/B - 82435 +/- 5. 
MP 203 = - 82450				FAIL
```

**Logic:** Value -82450 is NOT within [-82440, -82430] → **FAIL**

---

## Summary of Patterns

| Pattern Type | Example Syntax | Description |
|-------------|----------------|-------------|
| Exact Match | `S/B VALUE` | Value must exactly match (case-insensitive) |
| Tolerance | `S/B 100 +/- 5` | Value must be within target ± tolerance |
| Min-Max | `S/B 0 to 100` | Value must be in range [min, max] |
| Set | `S/B X or Y or Z` | Value must be one of the listed options |
| Range Expansion | `S/B X`<br>`X May be 1 - 9, A, B` | Expands ranges and combines values |
| Hex Range | `S/B 0000 to FFFF` | Hexadecimal range comparison |
| Blank Allowed | `S/B X or blank` | Empty/blank values are valid |
| Binary | `S/B 000 to 111` | String-based range comparison |
