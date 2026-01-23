# Pass-Fail Cleaner - Quick Reference Card

## How to Start
```
Double-click: run_gui.bat
```

## Basic Steps
1. Choose File or Folder
2. (Optional) Choose Output Folder
3. Click "Process Files"
4. Done!

## Button Guide

| Button | What It Does |
|--------|--------------|
| **Choose File** | Select one file to process |
| **Choose Folder** | Select a folder of files |
| **Include subfolders** | Also process files in subfolders |
| **Process Files** | Start the processing |

## Understanding Results

✓ **PASS** = Test passed  
⚠️ **FAIL** = Test failed (check line numbers)  
⚠️ **Unchanged** = Couldn't automatically check  

## Output Files

Original file: `test.txt`  
Processed file: `test_processed.txt`  

## Tips

- Original files are NEVER changed
- Test with 1 file before processing many
- Line numbers help you find problems
- Progress window shows everything happening

## Common Messages

**"No PASS/FAIL conditions found"**  
→ Normal - file has no test conditions

**"Processing complete! All tests passed."**  
→ Success! Everything is good

**"Failed tests: 5"**  
→ Check the line numbers shown in progress window

## Need Help?

See `GUI_USER_GUIDE.md` for detailed instructions
