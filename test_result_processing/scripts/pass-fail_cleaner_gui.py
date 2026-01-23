#!/usr/bin/env python3
"""
Pass-Fail Cleaner - Graphical User Interface
A simple, user-friendly interface for processing test result files.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import sys
from pathlib import Path
import importlib.util

# Import the processor from the main script
# Handle both hyphenated and underscored filenames
script_filename = None
for name in ['pass-fail_cleaner.py', 'pass_fail_cleaner.py']:
    script_path = Path(__file__).parent / name
    if script_path.exists():
        script_filename = name
        break

if script_filename is None:
    messagebox.showerror(
        "Error",
        "Could not find pass-fail_cleaner.py or pass_fail_cleaner.py\n\n"
        "Please make sure both files are in the same folder."
    )
    sys.exit(1)

try:
    # Load the module dynamically to handle hyphenated filenames
    spec = importlib.util.spec_from_file_location("cleaner_module", script_path)
    cleaner_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cleaner_module)
    TestResultProcessor = cleaner_module.TestResultProcessor
    process_directory = cleaner_module.process_directory
except Exception as e:
    messagebox.showerror(
        "Error",
        f"Could not load pass-fail_cleaner.py\n\n"
        f"Error: {str(e)}\n\n"
        "Please make sure the file is not corrupted."
    )
    sys.exit(1)


class PassFailCleanerGUI:
    """Simple GUI for the Pass-Fail Cleaner script."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Pass-Fail Cleaner")
        self.root.geometry("580x680")
        
        # Make window non-resizable for simplicity
        self.root.resizable(False, False)
        
        # Variables
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.recursive_var = tk.BooleanVar(value=False)
        self.processing = False
        
        # Create UI
        self.create_widgets()
        
    def create_widgets(self):
        """Create all GUI widgets."""
        
        # Configure root window to expand
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Main container with tighter padding
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure main frame to expand
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)  # Progress section expands
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="Pass-Fail Cleaner",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 5))
        
        # Description
        desc_label = ttk.Label(
            main_frame,
            text="Process test files and resolve PASS/FAIL conditions automatically",
            font=("Arial", 10)
        )
        desc_label.grid(row=1, column=0, columnspan=3, pady=(0, 15))
        
        # Input section
        input_frame = ttk.LabelFrame(main_frame, text="Input", padding="10")
        input_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 8))
        
        # Configure input frame to expand
        input_frame.columnconfigure(0, weight=1)
        
        ttk.Label(input_frame, text="Select file or folder:").grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        ttk.Entry(input_frame, textvariable=self.input_path).grid(
            row=1, column=0, sticky=(tk.W, tk.E), padx=(0, 5)
        )
        
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=1, column=1)
        
        ttk.Button(
            button_frame,
            text="Choose File",
            command=self.browse_file
        ).grid(row=0, column=0, padx=(0, 5))
        
        ttk.Button(
            button_frame,
            text="Choose Folder",
            command=self.browse_folder
        ).grid(row=0, column=1)
        
        # Recursive checkbox
        ttk.Checkbutton(
            input_frame,
            text="Include subfolders (when processing a folder)",
            variable=self.recursive_var
        ).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        
        # Output section
        output_frame = ttk.LabelFrame(main_frame, text="Output (Optional)", padding="10")
        output_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 8))
        
        # Configure output frame to expand
        output_frame.columnconfigure(0, weight=1)
        
        ttk.Label(
            output_frame,
            text="Save results to folder (leave empty to save next to original files):"
        ).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        ttk.Entry(output_frame, textvariable=self.output_path).grid(
            row=1, column=0, sticky=(tk.W, tk.E), padx=(0, 5)
        )
        
        ttk.Button(
            output_frame,
            text="Choose Folder",
            command=self.browse_output
        ).grid(row=1, column=1)
        
        # Process button
        self.process_button = ttk.Button(
            main_frame,
            text="Process Files",
            command=self.process_files,
            style="Accent.TButton"
        )
        self.process_button.grid(row=4, column=0, columnspan=3, pady=(8, 8), ipadx=20, ipady=5)
        
        # Progress section
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 8))
        
        # Text area for output
        self.output_text = scrolledtext.ScrolledText(
            progress_frame,
            height=13,
            wrap=tk.WORD,
            state='disabled',
            font=("Courier", 9)
        )
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(
            main_frame,
            mode='indeterminate'
        )
        self.progress_bar.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 8))
        
        # Status label
        self.status_label = ttk.Label(
            main_frame,
            text="Ready",
            font=("Arial", 9)
        )
        self.status_label.grid(row=7, column=0, columnspan=3)
    
    def browse_file(self):
        """Open file browser to select a single file."""
        filename = filedialog.askopenfilename(
            title="Select Test File",
            filetypes=[
                ("Text Files", "*.txt *.TXT"),
                ("All Files", "*.*")
            ]
        )
        if filename:
            self.input_path.set(filename)
            self.log(f"Selected file: {filename}\n")
            
    def browse_folder(self):
        """Open folder browser to select a directory."""
        foldername = filedialog.askdirectory(
            title="Select Folder Containing Test Files"
        )
        if foldername:
            self.input_path.set(foldername)
            self.log(f"Selected folder: {foldername}\n")
            
    def browse_output(self):
        """Open folder browser to select output directory."""
        foldername = filedialog.askdirectory(
            title="Select Output Folder"
        )
        if foldername:
            self.output_path.set(foldername)
            self.log(f"Output folder: {foldername}\n")
            
    def log(self, message):
        """Add message to the output text area."""
        self.output_text.config(state='normal')
        self.output_text.insert(tk.END, message)
        self.output_text.see(tk.END)
        self.output_text.config(state='disabled')
        self.root.update_idletasks()
        
    def clear_log(self):
        """Clear the output text area."""
        self.output_text.config(state='normal')
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state='disabled')
        
    def set_status(self, message):
        """Update the status label."""
        self.status_label.config(text=message)
        self.root.update_idletasks()
        
    def process_files(self):
        """Process the selected file(s)."""
        if self.processing:
            messagebox.showwarning(
                "Already Processing",
                "Please wait for the current operation to complete."
            )
            return
            
        input_path = self.input_path.get().strip()
        
        if not input_path:
            messagebox.showerror(
                "No Input Selected",
                "Please select a file or folder to process."
            )
            return
            
        if not Path(input_path).exists():
            messagebox.showerror(
                "File Not Found",
                f"The selected path does not exist:\n{input_path}"
            )
            return
            
        # Start processing in a separate thread to keep GUI responsive
        self.processing = True
        self.process_button.config(state='disabled')
        self.progress_bar.start(10)
        self.clear_log()
        self.set_status("Processing...")
        
        thread = threading.Thread(target=self.run_processing)
        thread.daemon = True
        thread.start()
        
    def run_processing(self):
        """Run the actual processing (in separate thread)."""
        try:
            input_path = Path(self.input_path.get().strip())
            output_path = self.output_path.get().strip() or None
            recursive = self.recursive_var.get()
            
            processor = TestResultProcessor()
            
            if input_path.is_file():
                # Process single file
                self.log(f"Processing file: {input_path}\n")
                self.log("-" * 60 + "\n\n")
                
                if output_path:
                    output_file = Path(output_path) / f"{input_path.stem}_processed{input_path.suffix}"
                else:
                    output_file = input_path.parent / f"{input_path.stem}_processed{input_path.suffix}"
                
                # Check if file has PASS/FAIL conditions
                if not processor.has_pass_fail_conditions(str(input_path)):
                    self.log("No PASS/FAIL conditions found in this file.\n")
                    self.log("No output file created.\n")
                    self.show_completion_message(0, 0, 0, 0)
                    return
                
                stats = processor.process_file(str(input_path), str(output_file))
                
                self.log("\nProcessing complete!\n")
                self.log(f"Total PASS/FAIL instances: {stats['total']}\n")
                self.log(f"  - Resolved as PASS: {stats['passed']}\n")
                self.log(f"  - Resolved as FAIL: {stats['failed']}\n")
                if stats['failed'] > 0:
                    self.log(f"    Line numbers: {', '.join(map(str, stats['failed_lines']))}\n")
                self.log(f"  - Left unchanged: {stats['unchanged']}\n")
                if stats['unchanged'] > 0:
                    self.log(f"    Line numbers: {', '.join(map(str, stats['unchanged_lines']))}\n")
                self.log(f"\nOutput saved to:\n{output_file}\n")
                
                self.show_completion_message(1, stats['total'], stats['failed'], stats['unchanged'])
                
            elif input_path.is_dir():
                # Process directory
                self.log(f"Processing folder: {input_path}\n")
                if recursive:
                    self.log("Mode: Including subfolders\n")
                else:
                    self.log("Mode: Current folder only\n")
                self.log("=" * 60 + "\n\n")
                
                total_stats = process_directory(str(input_path), recursive, output_path)
                
                self.log("\n" + "=" * 60 + "\n")
                self.log("Processing complete!\n")
                self.log(f"Files checked: {total_stats['files_checked']}\n")
                self.log(f"Files processed: {total_stats['files_processed']}\n")
                self.log(f"Files skipped (no PASS/FAIL): {total_stats['files_skipped']}\n\n")
                self.log(f"Total PASS/FAIL instances: {total_stats['total_instances']}\n")
                self.log(f"  - Resolved as PASS: {total_stats['total_passed']}\n")
                self.log(f"  - Resolved as FAIL: {total_stats['total_failed']}\n")
                self.log(f"  - Left unchanged: {total_stats['total_unchanged']}\n")
                
                self.show_completion_message(
                    total_stats['files_processed'],
                    total_stats['total_instances'],
                    total_stats['total_failed'],
                    total_stats['total_unchanged']
                )
            else:
                self.log("Error: Invalid path (not a file or folder)\n")
                messagebox.showerror(
                    "Invalid Path",
                    "The selected path is not a valid file or folder."
                )
                
        except Exception as e:
            self.log(f"\nError: {str(e)}\n")
            messagebox.showerror(
                "Processing Error",
                f"An error occurred while processing:\n\n{str(e)}"
            )
        finally:
            # Re-enable UI
            self.root.after(0, self.finish_processing)
            
    def finish_processing(self):
        """Clean up after processing is complete."""
        self.processing = False
        self.process_button.config(state='normal')
        self.progress_bar.stop()
        self.set_status("Ready")
        
    def show_completion_message(self, files_processed, total_instances, failed, unchanged):
        """Show completion message box with summary."""
        if files_processed == 0:
            message = "No files with PASS/FAIL conditions were found."
        elif failed == 0 and unchanged == 0:
            message = (
                f"Success! All {total_instances} test(s) passed.\n\n"
                f"Processed {files_processed} file(s)."
            )
        else:
            message = (
                f"Processing complete!\n\n"
                f"Processed {files_processed} file(s)\n"
                f"Total tests: {total_instances}\n"
            )
            if failed > 0:
                message += f"⚠️ Failed tests: {failed}\n"
            if unchanged > 0:
                message += f"⚠️ Unchanged tests: {unchanged}\n"
            message += "\nCheck the progress window for details."
            
        messagebox.showinfo("Processing Complete", message)


def main():
    """Main entry point for the GUI."""
    root = tk.Tk()
    
    # Try to set a nice theme if available
    try:
        style = ttk.Style()
        style.theme_use('clam')  # Use a modern theme
    except:
        pass
    
    app = PassFailCleanerGUI(root)
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()


if __name__ == '__main__':
    main()
