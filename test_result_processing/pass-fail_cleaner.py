#!/usr/bin/env python3
"""
Pass-Fail Cleaner
Processes test result files and resolves PASS/FAIL conditions based on criteria.

This script identifies lines ending with PASS/FAIL and determines the actual result
by comparing the measured value against the expected criteria ("S/B" = Should Be).

Usage:
  Single file:    python pass-fail_cleaner.py input.txt [output.txt]
  Directory:      python pass-fail_cleaner.py /path/to/logs/
  Recursive:      python pass-fail_cleaner.py -r /path/to/logs/
  
Only creates output files for inputs that contain PASS/FAIL conditions.
"""

import re
import sys
import os
from pathlib import Path
from typing import List, Tuple, Optional


class TestResultProcessor:
    """Process test result files to resolve PASS/FAIL conditions."""
    
    def __init__(self):
        self.criteria_pattern = re.compile(r'S/B\s+(.+?)(?:\s*\n|$)', re.IGNORECASE)
        # Match PASS/FAIL with optional trailing asterisks or other characters
        self.pass_fail_pattern = re.compile(r'^(.+?)\s+(PASS/FAIL)[\*\s]*$')
        self.previous_values = {}  # Track previous values for "greater than previous" comparisons
        self.file_lines = []  # Store file lines for cross-reference lookups
        self.current_line_idx = 0  # Track current line being processed
        
    def extract_value(self, line: str) -> Optional[str]:
        """Extract the measured value from a line."""
        # Look for pattern like "MP XXX = VALUE" followed by PASS/FAIL
        # Need to exclude the PASS/FAIL part (with optional trailing asterisks or other chars)
        # First, remove the PASS/FAIL portion
        line_without_result = re.sub(r'\s+PASS/FAIL[\*\s]*$', '', line)
        
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
    
    def find_reference_value(self, reference_name: str, lines: List[str], current_line_idx: int) -> Optional[str]:
        """
        Find the value of a reference parameter in the file.
        
        Searches backwards from current line for pattern: REFERENCE_NAME = VALUE
        
        Args:
            reference_name: The reference to look for (e.g., "VEN2.01/02")
            lines: All lines from the file
            current_line_idx: Index of current PASS/FAIL line
            
        Returns:
            The reference value, or None if not found
        """
        # Search backwards from current position
        for i in range(current_line_idx - 1, -1, -1):
            line = lines[i].strip()
            # Look for pattern: REFERENCE_NAME = VALUE
            # Use regex to handle various spacing
            pattern = re.escape(reference_name) + r'\s*=\s*(.+?)(?:\s|$)'
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                return value
        return None
    
    def has_pass_fail_conditions(self, file_path: str) -> bool:
        """
        Check if a file contains any PASS/FAIL conditions.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if file contains PASS/FAIL, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='windows-1252') as f:
                for line in f:
                    if self.pass_fail_pattern.match(line.rstrip()):
                        return True
            return False
        except Exception as e:
            print(f"Warning: Could not check {file_path}: {e}", file=sys.stderr)
            return False
    
    def parse_criteria(self, criteria_text: str) -> dict:
        """
        Parse criteria text to determine test requirements.
        
        Returns a dict with:
        - 'type': 'exact', 'range', 'tolerance', 'set', 'min_max'
        - 'values': relevant values for comparison
        """
        criteria = criteria_text.strip()
        
        # Handle cross-reference pattern: "S/B = REFERENCE" (e.g., "= VEN2.01/02" or "= 30000")
        # This means the value should match either:
        # - The value stored in REFERENCE elsewhere in the file (if REFERENCE is a parameter name)
        # - The literal value REFERENCE (if REFERENCE is just a number)
        if criteria.startswith('='):
            reference = criteria[1:].strip()
            # Check if it's a parameter reference (contains letters/dots/slashes) or a direct value (just digits)
            if re.search(r'[A-Za-z]', reference) or '/' in reference or '.' in reference:
                # It's a cross-reference to another parameter
                return {'type': 'cross_reference', 'reference': reference}
            else:
                # It's a direct value comparison (numeric)
                return {'type': 'exact', 'value': reference}
        
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
    
    def extract_numeric_value(self, value_str: str) -> Optional[float]:
        """
        Extract numeric value from a string that may contain units.
        Examples: "136.974944 Deg" -> 136.974944, "-22.5" -> -22.5
        """
        # Remove common units and extra spaces
        cleaned = value_str.replace(' ', '').strip()
        
        # Try to extract just the numeric part
        # Match optional sign, digits, optional decimal point and more digits
        match = re.match(r'([+-]?\d+(?:\.\d+)?)', cleaned)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None
    
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
        
        # Handle "cross_reference" type (e.g., S/B = VEN2.01/02)
        if criteria['type'] == 'cross_reference':
            reference_name = criteria['reference']
            # Find the reference value in the file
            reference_value = self.find_reference_value(reference_name, self.file_lines, self.current_line_idx)
            
            if reference_value is None:
                # Can't find reference, can't validate
                return None
            
            # Normalize both values for comparison
            # Remove spaces, colons, and convert to lowercase for case-insensitive comparison
            value_normalized = value.replace(' ', '').replace(':', '').lower()
            ref_normalized = reference_value.replace(' ', '').replace(':', '').lower()
            
            # Also try comparing as hex numbers (strip leading zeros)
            # This handles cases like "00629" vs "629" or "001D" vs "1d"
            try:
                # Try to convert both as hex numbers
                value_hex = int(value_normalized, 16)
                ref_hex = int(ref_normalized, 16)
                return value_hex == ref_hex
            except ValueError:
                # Not valid hex, fall back to string comparison
                return value_normalized == ref_normalized
        
        # Handle "greater_than_previous" type
        if criteria['type'] == 'greater_than_previous':
            param_name = criteria['param']
            
            # Check if we have a previous value
            if param_name not in self.previous_values:
                # No previous value - this is the first occurrence, so it passes
                return True
            
            current_val = self.extract_numeric_value(value)
            if current_val is None:
                # Can't extract numeric value
                return None
            
            try:
                previous_val = self.previous_values[param_name]
                return current_val > previous_val
            except (TypeError, KeyError):
                # If we can't compare, can't validate
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
            val = self.extract_numeric_value(value)
            if val is None:
                return False
            return val > criteria['threshold']
        
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
            # Extract numeric value, handling units like "Deg", "Hz", etc.
            val = self.extract_numeric_value(value)
            if val is None:
                return False
            
            target = criteria['target']
            tolerance = criteria['tolerance']
            return target - tolerance <= val <= target + tolerance
        
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
        # Use latin-1 encoding which maps bytes 0-255 directly to Unicode code points
        # This preserves all characters including Windows-1252 special chars (en-dash, etc.)
        with open(input_file, 'r', encoding='windows-1252') as f:
            lines = f.readlines()
        
        # Store lines for cross-reference lookups
        self.file_lines = lines
        
        stats = {'total': 0, 'passed': 0, 'failed': 0, 'unchanged': 0, 'failed_lines': [], 'unchanged_lines': []}
        processed_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Update current line index for cross-reference lookups
            self.current_line_idx = i
            
            # Check if this line ends with PASS/FAIL
            match = self.pass_fail_pattern.match(line.rstrip())
            if match:
                stats['total'] += 1
                
                # Extract the line content without PASS/FAIL
                line_content = match.group(1)
                
                # Look for the criteria line (S/B)
                # First check if the PASS/FAIL line itself contains S/B (e.g., "MP 285 S/B = VEN2.01/02 PASS/FAIL")
                criteria_text = None
                criteria_line_idx = None
                
                # For lines with S/B on the PASS/FAIL line itself, extract from line_content (which has PASS/FAIL removed)
                criteria_match = self.criteria_pattern.search(line_content)
                if criteria_match:
                    # Criteria is on the PASS/FAIL line itself (after removing PASS/FAIL)
                    criteria_text = criteria_match.group(1).strip()
                    criteria_line_idx = i
                else:
                    # Look backwards for the criteria line
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
                    criteria = self.parse_criteria(criteria_text)
                    
                    # For cross_reference type, we need to find the actual measured value
                    # The PASS/FAIL line format is: "PARAM S/B = REFERENCE"
                    # We need to find the line with: "PARAM = VALUE" or "PARAM: VALUE"
                    if criteria['type'] == 'cross_reference':
                        # Extract parameter name from the PASS/FAIL line
                        # Line format: "MP 285 S/B = VEN2.01/02 PASS/FAIL"
                        param_match = re.match(r'^(.+?)\s+S/B\s*=', line_content)
                        if param_match:
                            param_name = param_match.group(1).strip()
                            
                            # Look backwards for the value line: "PARAM = VALUE" or "PARAM: VALUE"
                            # Use STRICT matching - only accept exact parameter name matches
                            value = None
                            for j in range(i - 1, max(i - 20, -1), -1):
                                # Look for lines with this exact param and = or : but not S/B
                                if param_name in lines[j] and ('=' in lines[j] or ':' in lines[j]) and 'S/B' not in lines[j]:
                                    # Extract the value (after = or :)
                                    val_match = re.search(r'[=:]\s*(.*)$', lines[j].strip())
                                    if val_match:
                                        value = val_match.group(1).strip()
                                        break
                        else:
                            value = None
                    else:
                        # For other criteria types, extract value from the PASS/FAIL line itself
                        value = self.extract_value(line)
                    
                    if value is not None:
                        passed = self.check_value_against_criteria(value, criteria)
                        
                        # If None is returned, we can't validate - leave unchanged
                        if passed is None:
                            processed_lines.append(line)
                            stats['unchanged'] += 1
                            stats['unchanged_lines'].append(i + 1)  # Line numbers are 1-indexed
                        else:
                            result = "PASS" if passed else "FAIL"
                            
                            if passed:
                                stats['passed'] += 1
                            else:
                                stats['failed'] += 1
                                stats['failed_lines'].append(i + 1)  # Line numbers are 1-indexed
                            
                            # Reconstruct the line with the result
                            # Replace PASS/FAIL (with any trailing asterisks/spaces but not newlines) with clean result
                            processed_line = re.sub(r'PASS/FAIL[\* ]*', result, line)
                            processed_lines.append(processed_line)
                        
                        # Store this value for future "greater than previous" comparisons
                        param_name = self.extract_param_name(line)
                        if param_name and value:
                            # Try to extract numeric value (handles units like "Deg", "Hz", etc.)
                            numeric_value = self.extract_numeric_value(value)
                            if numeric_value is not None:
                                self.previous_values[param_name] = numeric_value
                            else:
                                # Store as string if not numeric
                                self.previous_values[param_name] = value
                    else:
                        # Could not extract value, leave as PASS/FAIL
                        processed_lines.append(line)
                        stats['unchanged'] += 1
                        stats['unchanged_lines'].append(i + 1)  # Line numbers are 1-indexed
                else:
                    # No criteria found, leave as PASS/FAIL
                    processed_lines.append(line)
                    stats['unchanged'] += 1
                    stats['unchanged_lines'].append(i + 1)  # Line numbers are 1-indexed
            else:
                # Regular line, keep as-is
                processed_lines.append(line)
            
            i += 1
        
        # Write output file
        # Use latin-1 encoding to preserve special characters from input
        with open(output_file, 'w', encoding='windows-1252') as f:
            f.writelines(processed_lines)
        
        return stats


def process_directory(directory: str, recursive: bool = False, output_dir: str = None) -> dict:
    """
    Process all files in a directory.
    
    Args:
        directory: Path to directory containing log files
        recursive: If True, process subdirectories recursively
        output_dir: Optional output directory (defaults to same as input)
        
    Returns:
        Dictionary with processing statistics
    """
    processor = TestResultProcessor()
    dir_path = Path(directory)
    
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    if not dir_path.is_dir():
        raise ValueError(f"Not a directory: {directory}")
    
    # Find all files
    if recursive:
        files = [f for f in dir_path.rglob('*') if f.is_file()]
    else:
        files = [f for f in dir_path.iterdir() if f.is_file()]
    
    # Filter to only files with PASS/FAIL conditions
    files_to_process = []
    for file_path in files:
        if processor.has_pass_fail_conditions(str(file_path)):
            files_to_process.append(file_path)
    
    if not files_to_process:
        print(f"No files with PASS/FAIL conditions found in {directory}")
        return {'files_checked': len(files), 'files_processed': 0, 'files_skipped': len(files)}
    
    print(f"Found {len(files_to_process)} file(s) with PASS/FAIL conditions (out of {len(files)} total)")
    print("=" * 60)
    
    total_stats = {
        'files_checked': len(files),
        'files_processed': 0,
        'files_skipped': len(files) - len(files_to_process),
        'total_instances': 0,
        'total_passed': 0,
        'total_failed': 0,
        'total_unchanged': 0
    }
    
    for file_path in files_to_process:
        # Determine output path
        if output_dir:
            output_path = Path(output_dir)
            # Preserve subdirectory structure if recursive
            if recursive:
                rel_path = file_path.relative_to(dir_path)
                output_path = output_path / rel_path.parent
            output_path.mkdir(parents=True, exist_ok=True)
            output_file = output_path / f"{file_path.stem}_processed{file_path.suffix}"
        else:
            output_file = file_path.parent / f"{file_path.stem}_processed{file_path.suffix}"
        
        print(f"\nProcessing: {file_path}")
        print(f"Output to:  {output_file}")
        
        try:
            stats = processor.process_file(str(file_path), str(output_file))
            
            print(f"  ✓ {stats['total']} instances: {stats['passed']} PASS, {stats['failed']} FAIL, {stats['unchanged']} unchanged")
            
            # Show line numbers for failures and unchanged
            if stats['failed'] > 0:
                print(f"    FAIL at lines: {', '.join(map(str, stats['failed_lines']))}")
            if stats['unchanged'] > 0:
                print(f"    Unchanged at lines: {', '.join(map(str, stats['unchanged_lines']))}")
            
            total_stats['files_processed'] += 1
            total_stats['total_instances'] += stats['total']
            total_stats['total_passed'] += stats['passed']
            total_stats['total_failed'] += stats['failed']
            total_stats['total_unchanged'] += stats['unchanged']
            
        except Exception as e:
            print(f"  ✗ Error: {e}", file=sys.stderr)
    
    return total_stats


def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Single file:  python pass-fail_cleaner.py <input_file> [output_file]")
        print("  Directory:    python pass-fail_cleaner.py <directory> [output_directory]")
        print("  Recursive:    python pass-fail_cleaner.py -r <directory> [output_directory]")
        print("\nProcesses test result files to resolve PASS/FAIL conditions.")
        print("Only creates output files for inputs that contain PASS/FAIL conditions.")
        sys.exit(1)
    
    # Check for recursive flag
    recursive = False
    arg_offset = 1
    if sys.argv[1] == '-r':
        recursive = True
        arg_offset = 2
        if len(sys.argv) < 3:
            print("Error: -r flag requires a directory path")
            sys.exit(1)
    
    input_path = sys.argv[arg_offset]
    output_path = sys.argv[arg_offset + 1] if len(sys.argv) > arg_offset + 1 else None
    
    # Determine if input is file or directory
    path = Path(input_path)
    
    if not path.exists():
        print(f"Error: Path not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    
    processor = TestResultProcessor()
    
    try:
        if path.is_dir():
            # Process directory
            print(f"Processing directory: {input_path}")
            if recursive:
                print("Mode: Recursive")
            if output_path:
                print(f"Output directory: {output_path}")
            print("=" * 60)
            
            stats = process_directory(input_path, recursive, output_path)
            
            print("\n" + "=" * 60)
            print("Processing complete!")
            print(f"Files checked: {stats['files_checked']}")
            print(f"Files processed: {stats['files_processed']}")
            print(f"Files skipped (no PASS/FAIL): {stats['files_skipped']}")
            if stats['files_processed'] > 0:
                print(f"\nTotal PASS/FAIL instances: {stats['total_instances']}")
                print(f"  - Resolved as PASS: {stats['total_passed']}")
                print(f"  - Resolved as FAIL: {stats['total_failed']}")
                print(f"  - Left unchanged: {stats['total_unchanged']}")
        
        else:
            # Process single file
            # First check if it has PASS/FAIL conditions
            if not processor.has_pass_fail_conditions(input_path):
                print(f"No PASS/FAIL conditions found in {input_path}")
                print("No output file created.")
                sys.exit(0)
            
            # Generate output filename if not specified
            if output_path:
                output_file = output_path
            else:
                output_file = str(path.parent / f"{path.stem}_processed{path.suffix}")
            
            print(f"Processing: {input_path}")
            print(f"Output to: {output_file}")
            print("-" * 60)
            
            stats = processor.process_file(input_path, output_file)
            
            print("\nProcessing complete!")
            print(f"Total PASS/FAIL instances found: {stats['total']}")
            print(f"  - Resolved as PASS: {stats['passed']}")
            print(f"  - Resolved as FAIL: {stats['failed']}")
            if stats['failed'] > 0:
                print(f"    Line numbers: {', '.join(map(str, stats['failed_lines']))}")
            print(f"  - Left unchanged: {stats['unchanged']}")
            if stats['unchanged'] > 0:
                print(f"    Line numbers: {', '.join(map(str, stats['unchanged_lines']))}")
            print(f"\nOutput written to: {output_file}")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
