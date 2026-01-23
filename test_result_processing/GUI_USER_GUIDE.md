# Pass-Fail Cleaner GUI - User Guide

## Quick Start

1. **Double-click** `run_gui.bat` (Windows) or run `python pass-fail_cleaner_gui.py`
2. Click **"Choose File"** or **"Choose Folder"** to select what to process
3. (Optional) Click **"Choose Folder"** in the Output section to save results elsewhere
4. Click **"Process Files"** button
5. Watch the progress and see results!

## What Each Button Does

### Choose File
- Click this to process a **single test file**
- A window will open where you can browse and select one file
- The file path will appear in the input box

### Choose Folder
- Click this to process **multiple files at once**
- Select a folder containing your test files
- All files in that folder will be checked

### Include Subfolders
- Check this box if you want to also process files in **subfolders**
- Only works when processing a folder (not a single file)
- Unchecked = only process files in the selected folder

### Output Folder (Optional)
- Leave empty = processed files are saved next to the original files
- Or click "Choose Folder" to save all processed files to a different location

### Process Files
- Click this button to **start processing**
- The program will show progress in the window below
- A message will appear when complete

## Understanding the Results

### What You'll See

The progress window shows:
- Which files are being processed
- How many PASS/FAIL conditions were found
- How many were resolved as PASS or FAIL
- Any line numbers where problems occurred

### Output Files

Processed files are saved with `_processed` added to the filename:
- Original: `A0807XMP_SFF.TXT`
- Processed: `A0807XMP_SFF_processed.TXT`

### What the Numbers Mean

- **PASS**: Test condition was checked and passed ✓
- **FAIL**: Test condition was checked and failed ⚠️
- **Unchanged**: Test condition couldn't be automatically checked

### When Tests Fail

If any tests show as FAIL, the line numbers are displayed so you can:
1. Open the processed file
2. Go to those line numbers
3. Review what failed

## Common Questions

**Q: What files can I process?**
- Any text file (.txt, .TXT)
- Files must contain "PASS/FAIL" conditions to be processed

**Q: Will my original files be changed?**
- No! Original files are never modified
- New files with `_processed` in the name are created

**Q: What if no PASS/FAIL conditions are found?**
- The program will tell you and won't create an output file
- This is normal for files that don't have test conditions

**Q: Can I process hundreds of files at once?**
- Yes! Just select the folder containing all the files
- Use "Include subfolders" if files are in multiple folders

**Q: What if I get an error?**
- Check that the file path is correct
- Make sure you have permission to read the files
- Try processing just one file first to test

## Troubleshooting

### "No Input Selected"
→ You need to choose a file or folder first

### "File Not Found"
→ The file path doesn't exist - try selecting it again

### "No PASS/FAIL conditions found"
→ This file doesn't have any test conditions to process - this is normal

### "Could not find pass-fail_cleaner.py"
→ Make sure both GUI and script files are in the same folder

## Tips

- **Test with one file first** before processing many files
- **Check the progress window** for detailed information
- **Line numbers** help you find specific issues in large files
- **Use output folder** when processing many files to keep them organized

## Need Help?

The program shows helpful messages when:
- Something goes wrong
- Processing is complete
- Files are found or not found

Just read the messages - they're written in plain English!
