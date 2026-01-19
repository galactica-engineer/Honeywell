#!/usr/bin/env python3
"""
Test Result Cleaner
Processes test result files and resolves PASS/FAIL conditions based on criteria.

This script identifies lines ending with PASS/FAIL and determines the actual result
by comparing the measured value against the expected criteria ("S/B" = Should Be).
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple, Optional


class TestResultProcessor:
    """Process test result files to resolve PASS/FAIL conditions."""
    
    def __init__(self):
        self.criteria_pattern = re.compile(r'S/B\s+(.+?)(?:\s*\n|$)', re.IGNORECASE)
        self.pass_fail_pattern = re.compile(r'^(.+?)\s+(PASS/FAIL)\s*$')
        self.previous_values = {}  # Track previous values for "greater than previous" comparisons
        
    def extract_value(self, line: str) -> Optional[str]:
        """Extract the measured value from a line."""
        # Look for pattern like "MP XXX = VALUE" followed by PASS/FAIL
        # Need to exclude the PASS/FAIL part
        # First, remove the PASS/FAIL portion
        line_without_result = re.sub(r'\s+PASS/FAIL\s*$', '', line)
        
        # Now extract the value after = (use .* to allow empty values)
        match = re.search(r'=\s*(.*)$', line_without_result)
        if match:
            value = match.group(1).strip()
            return value
        return None
    
    def extract_param_name(self, line: str) -> Optional[str]:
        """Extract the parameter name from a line (e.g., 'MP 214' from 'MP 214 = 425790')."""
        # Match pattern like "MP 214" or "I-1.02" before the =
        match = re.match(r'^(.+?)\s*=', line)
        if match:
            return match.group(1).strip()
        return None
    
    def parse_criteria(self, criteria_text: str) -> dict:
        """
        Parse criteria text to determine test requirements.
        
        Returns a dict with:
        - 'type': 'exact', 'range', 'tolerance', 'set', 'min_max'
        - 'values': relevant values for comparison
        """
        criteria = criteria_text.strip()
        
        # Handle "in range of X to Y and X to Y" or similar complex patterns (check this FIRST)
        if 'in range of' in criteria.lower():
            # Check for "or DSABLD" or similar alternatives at the end
            or_match = re.search(r'\s+or\s+(\w+)\s*$', criteria, re.IGNORECASE)
            alternative = or_match.group(1) if or_match else None
            
            # For now, just mark these as always pass (they're complex IP/netmask validations)
            # A proper implementation would parse the dual ranges
            return {'type': 'complex_range', 'alternative': alternative}
        
        # Handle "X to Y" range (e.g., "0 to 604799", "0000 to FFFF")
        if ' to ' in criteria.lower() and 'may be' not in criteria.lower():
            match = re.match(r'(.+?)\s+to\s+(.+)', criteria, re.IGNORECASE)
            if match:
                return {'type': 'range', 'min': match.group(1).strip(), 'max': match.group(2).strip()}
        
        # Handle "X - Y" range format (e.g., "0 - 9999.9")
        # Only match if it's clearly a numeric range, not part of other text
        if re.match(r'^\s*[+-]?\d+(?:\.\d+)?\s*-\s*[+-]?\d+(?:\.\d+)?\s*$', criteria):
            parts = re.split(r'\s*-\s*', criteria.strip())
            if len(parts) == 2:
                return {'type': 'range', 'min': parts[0].strip(), 'max': parts[1].strip()}
        
        # Handle "greater than previous" - extract which parameter to compare
        if 'greater than previous' in criteria.lower():
            # Extract the parameter name (e.g., "MP 214" from "Greater Than Previous MP 214")
            match = re.search(r'greater than previous\s+(.*)', criteria, re.IGNORECASE)
            if match:
                param_name = match.group(1).strip()
                return {'type': 'greater_than_previous', 'param': param_name}
            return {'type': 'unvalidatable'}
        
        # Handle ">" (greater than) operator
        if criteria.strip().startswith('>'):
            match = re.match(r'>\s*([+-]?\d+(?:\.\d+)?)', criteria.strip())
            if match:
                threshold = float(match.group(1))
                return {'type': 'greater_than', 'threshold': threshold}
        
        # Handle "+/-" tolerance (e.g., "27535 +/- 5")
        if '+/-' in criteria or '±' in criteria:
            match = re.match(r'([+-]?\s*\d+(?:\.\d+)?)\s*(?:\+/-|±)\s*(\d+(?:\.\d+)?)', criteria)
            if match:
                target = float(match.group(1).replace(' ', ''))
                tolerance = float(match.group(2))
                return {'type': 'tolerance', 'target': target, 'tolerance': tolerance}
        
        # Handle "X May be..." patterns (check this BEFORE general "or" pattern)
        if 'may be' in criteria.lower():
            match = re.search(r'may be\s+(.+)', criteria, re.IGNORECASE)
            if match:
                range_text = match.group(1).strip()
                # Check for combined range and values like "1 - 9, A, B or C"
                if (' - ' in range_text or ' to ' in range_text) and (',' in range_text or ' or ' in range_text):
                    # This is a mixed format - need to handle both range and individual values
                    values = []
                    # First split by 'or', then by comma
                    or_parts = re.split(r'\s+or\s+', range_text, flags=re.IGNORECASE)
                    for or_part in or_parts:
                        # Now split each part by comma
                        comma_parts = [p.strip() for p in or_part.split(',') if p.strip()]
                        for part in comma_parts:
                            # Check if this part contains a numeric range (use search to find range anywhere in string)
                            range_match = re.search(r'(\d+)\s*[-]+\s*(\d+)', part)
                            if range_match:
                                # Expand the range
                                start, end = range_match.groups()
                                try:
                                    # Numeric range
                                    for i in range(int(start), int(end) + 1):
                                        values.append(str(i))
                                except ValueError:
                                    # Keep as-is if not numeric
                                    values.append(part)
                            else:
                                # Only add if it's not just descriptive text
                                if not any(word in part.lower() for word in ['may be', 'x x', 'xx ', ' xx', 'xxx']):
                                    values.append(part)
                    return {'type': 'set', 'values': values}
                # Check for simple value list like "0 or 1" or "A, B, C"
                elif ' or ' in range_text or ',' in range_text:
                    # Split by 'or' first, then by comma
                    values = []
                    or_parts = re.split(r'\s+or\s+', range_text, flags=re.IGNORECASE)
                    for or_part in or_parts:
                        comma_parts = [p.strip() for p in or_part.split(',') if p.strip()]
                        values.extend(comma_parts)
                    return {'type': 'set', 'values': values}
                # Check for numeric range like "0 to 9"
                elif ' to ' in range_text:
                    match = re.match(r'(\d+)\s+to\s+(\d+)', range_text)
                    if match:
                        return {'type': 'range', 'min': match.group(1), 'max': match.group(2)}
                # Check for range like "00 to 79"
                elif '-' in range_text:
                    parts = re.split(r'\s*-\s*', range_text)
                    if len(parts) == 2:
                        return {'type': 'range', 'min': parts[0].strip(), 'max': parts[1].strip()}
        
        # Handle "or" separated values (e.g., "0 or 1", "0 or 9 or blank") - after checking for "may be"
        if ' or ' in criteria.lower():
            values = [v.strip() for v in re.split(r'\s+or\s+', criteria, flags=re.IGNORECASE)]
            return {'type': 'set', 'values': values}
        
        # Handle exact match
        return {'type': 'exact', 'value': criteria}
    
    def check_value_against_criteria(self, value: str, criteria: dict) -> bool:
        """
        Check if a value meets the criteria.
        
        Args:
            value: The measured value
            criteria: The parsed criteria dict
            
        Returns:
            True if the value passes, False otherwise
        """
        # Check for empty/blank values
        is_empty = not value or value.strip() == ''
        
        if is_empty:
            # Empty values pass if "blank" is in the allowed set
            if criteria['type'] == 'set' and any(v.lower() == 'blank' for v in criteria['values']):
                return True
            # Empty values fail for other criteria types
            if criteria['type'] != 'unvalidatable':
                return False
        
        # Handle patterns we can't validate - return None to leave unchanged
        if criteria['type'] == 'unvalidatable':
            return None
        
        # Handle "greater_than_previous" type
        if criteria['type'] == 'greater_than_previous':
            param_name = criteria['param']
            
            # Check if we have a previous value
            if param_name not in self.previous_values:
                # No previous value - this is the first occurrence, so it passes
                return True
            
            try:
                current_val = float(value.replace(' ', '').strip())
                previous_val = self.previous_values[param_name]
                return current_val > previous_val
            except (ValueError, TypeError):
                # If we can't convert to numbers, can't compare
                return None
        
        # Handle "complex_range" type (for IP addresses, netmasks)
        if criteria['type'] == 'complex_range':
            # If there's an alternative value and the value matches it, pass
            if criteria.get('alternative'):
                if value.upper().strip() == criteria['alternative'].upper():
                    return True
            
            # Parse the value as two octets with variable width
            # Format examples: "192168" (6 chars), "1101" (4 chars), "255  0" (6 chars with spaces)
            # The octets are formatted as 3-character fields, but leading spaces may be stripped
            value_clean = value.strip()
            
            # Values should be 4-6 characters
            if len(value_clean) < 4 or len(value_clean) > 6:
                return False
            
            try:
                # If exactly 6 chars, split into two 3-char fields
                if len(value_clean) == 6:
                    octet1_str = value_clean[0:3].strip()
                    octet2_str = value_clean[3:6].strip()
                # If 4-5 chars, need to find the split point
                # Format is typically: [1-3 digits][1-3 digits]
                else:
                    # Try to intelligently split - first octet is 1-3 digits from the start
                    # Second octet is the rest
                    # For "1101": split as "1" and "101" OR "11" and "01" OR "110" and "1"
                    # We need to try different splits and see which makes sense
                    found_valid = False
                    for split_point in range(1, len(value_clean)):
                        octet1_str = value_clean[:split_point]
                        octet2_str = value_clean[split_point:]
                        
                        try:
                            octet1 = int(octet1_str)
                            octet2 = int(octet2_str)
                            
                            # Both must be in valid range
                            if (0 <= octet1 <= 255) and (0 <= octet2 <= 255):
                                found_valid = True
                                break
                        except ValueError:
                            continue
                    
                    return found_valid
                
                # For 6-char values, validate the split octets
                octet1 = int(octet1_str)
                octet2 = int(octet2_str)
                
                # Both must be in range 0-255
                return (0 <= octet1 <= 255) and (0 <= octet2 <= 255)
            except (ValueError, IndexError):
                return False
        
        # Handle "greater_than" type
        if criteria['type'] == 'greater_than':
            try:
                val = float(value.replace(' ', '').strip())
                return val > criteria['threshold']
            except ValueError:
                return False
        
        if criteria['type'] == 'exact':
            return value.upper() == criteria['value'].upper()
        
        elif criteria['type'] == 'set':
            # Normalize for comparison
            value_normalized = value.upper().strip()
            return any(value_normalized == v.upper().strip() for v in criteria['values'])
        
        elif criteria['type'] == 'range':
            try:
                # Try numeric comparison first
                val = float(value.replace(' ', '').replace('-', '-').strip())
                min_val = float(criteria['min'].replace(' ', '').replace('-', '-').strip())
                max_val = float(criteria['max'].replace(' ', '').replace('-', '-').strip())
                return min_val <= val <= max_val
            except ValueError:
                # Fall back to string/hex comparison
                try:
                    val = int(value.replace(' ', ''), 16)
                    min_val = int(criteria['min'].replace(' ', ''), 16)
                    max_val = int(criteria['max'].replace(' ', ''), 16)
                    return min_val <= val <= max_val
                except:
                    # Last resort: alphabetic/string comparison
                    return criteria['min'] <= value <= criteria['max']
        
        elif criteria['type'] == 'tolerance':
            try:
                val = float(value.replace(' ', '').replace('-', '-').strip())
                target = criteria['target']
                tolerance = criteria['tolerance']
                return target - tolerance <= val <= target + tolerance
            except ValueError:
                return False
        
        return False
    
    def process_file(self, input_path: str, output_path: str) -> dict:
        """
        Process a test result file and resolve all PASS/FAIL conditions.
        
        Args:
            input_path: Path to input file
            output_path: Path to output file
            
        Returns:
            Dict with statistics: total, passed, failed
        """
        input_file = Path(input_path)
        output_file = Path(output_path)
        
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        # Read all lines
        with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        
        stats = {'total': 0, 'passed': 0, 'failed': 0, 'unchanged': 0}
        processed_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check if this line ends with PASS/FAIL
            match = self.pass_fail_pattern.match(line.rstrip())
            if match:
                stats['total'] += 1
                
                # Extract the line content without PASS/FAIL
                line_content = match.group(1)
                
                # Look backwards for the criteria line (S/B)
                criteria_text = None
                criteria_line_idx = None
                for j in range(i - 1, max(i - 10, -1), -1):
                    criteria_match = self.criteria_pattern.search(lines[j])
                    if criteria_match:
                        criteria_text = criteria_match.group(1).strip()
                        criteria_line_idx = j
                        
                        # Check if the criteria is just a placeholder (like "X" or "XX")
                        # and there's more explanation in the next line
                        if criteria_line_idx + 1 < len(lines):
                            next_line = lines[criteria_line_idx + 1].strip()
                            # Look for "May be" or other explanatory patterns
                            if 'may be' in next_line.lower() or (criteria_text in ['X', 'XX', 'XXX'] and next_line):
                                # Append the next line to criteria
                                criteria_text = criteria_text + ' ' + next_line
                        break
                
                # Determine pass/fail
                if criteria_text:
                    value = self.extract_value(line)
                    criteria = self.parse_criteria(criteria_text)
                    
                    if value is not None:
                        passed = self.check_value_against_criteria(value, criteria)
                        
                        # If None is returned, we can't validate - leave unchanged
                        if passed is None:
                            processed_lines.append(line)
                            stats['unchanged'] += 1
                        else:
                            result = "PASS" if passed else "FAIL"
                            
                            if passed:
                                stats['passed'] += 1
                            else:
                                stats['failed'] += 1
                            
                            # Reconstruct the line with the result
                            # Preserve the original whitespace/tab structure
                            processed_line = line.replace('PASS/FAIL', result)
                            processed_lines.append(processed_line)
                        
                        # Store this value for future "greater than previous" comparisons
                        param_name = self.extract_param_name(line)
                        if param_name and value:
                            try:
                                # Try to store as float for numeric comparisons
                                numeric_value = float(value.replace(' ', '').strip())
                                self.previous_values[param_name] = numeric_value
                            except ValueError:
                                # If not numeric, store as string
                                self.previous_values[param_name] = value
                    else:
                        # Could not extract value, leave as PASS/FAIL
                        processed_lines.append(line)
                        stats['unchanged'] += 1
                else:
                    # No criteria found, leave as PASS/FAIL
                    processed_lines.append(line)
                    stats['unchanged'] += 1
            else:
                # Regular line, keep as-is
                processed_lines.append(line)
            
            i += 1
        
        # Write output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(processed_lines)
        
        return stats


def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print("Usage: python test_result_cleaner.py <input_file> [output_file]")
        print("\nProcesses test result files to resolve PASS/FAIL conditions.")
        print("If output_file is not specified, uses <input_file>_cleaned.txt")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        # Generate output filename
        input_path = Path(input_file)
        output_file = str(input_path.parent / f"{input_path.stem}_cleaned{input_path.suffix}")
    
    print(f"Processing: {input_file}")
    print(f"Output to: {output_file}")
    print("-" * 60)
    
    processor = TestResultProcessor()
    
    try:
        stats = processor.process_file(input_file, output_file)
        
        print("\nProcessing complete!")
        print(f"Total PASS/FAIL instances found: {stats['total']}")
        print(f"  - Resolved as PASS: {stats['passed']}")
        print(f"  - Resolved as FAIL: {stats['failed']}")
        print(f"  - Left unchanged: {stats['unchanged']}")
        print(f"\nOutput written to: {output_file}")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
