import os
import sys
import argparse

# Function to list files based on extensions and ignore specific files
def list_files(root_dir, extensions=None, ignore_files=None, ignore_dirs=None):
    """List all files in the root directory with the specified extensions, ignoring specific files and directories."""
    files_to_include = []
    for foldername, subfolders, filenames in os.walk(root_dir):
        # Skip ignored directories
        if ignore_dirs and any(
            os.path.normpath(ignored_dir) in os.path.normpath(foldername) for ignored_dir in ignore_dirs
        ):
            continue

        for filename in filenames:
            # Skip ignored files
            if ignore_files and filename in ignore_files:
                continue
            if extensions:
                if any(filename.endswith(ext) for ext in extensions):
                    file_path = os.path.join(foldername, filename)
                    files_to_include.append(file_path)
            else:
                file_path = os.path.join(foldername, filename)
                files_to_include.append(file_path)
    return files_to_include

# Filter based on back-end or front-end
def filter_by_service(files_list, service_type):
    """Filter files by back-end or front-end services."""
    if service_type == "Back-End":
        return [f for f in files_list if "backend" in f.lower()]
    elif service_type == "Front-End":
        return [f for f in files_list if "frontend" in f.lower()]
    return files_list

# Save selected files' content into a text file
def save_code_to_text(files_list, output_file):
    """Save the selected files' content into a text file."""
    with open(output_file, "w", encoding="utf-8") as f_out:
        for file_path in files_list:
            f_out.write(f"### File: {file_path} ###\n\n")  # Add header with filename
            try:
                with open(file_path, "r", encoding="utf-8") as f_in:
                    f_out.write(f_in.read())  # Write file content
            except Exception as e:
                f_out.write(f"Could not read file {file_path}: {e}")
            f_out.write("\n\n" + "#" * 40 + "\n\n")  # Add a separator between files

def main():
    # Configure root directory and output file
    root_directory = r"C:\Users\jorda\OneDrive\Desktop\Code & Ai\email_parser_demo"  # Update this path if needed
    output_file = r"tools\codebase.txt"  # Output file for LLM input

    extensions = [
        ".py",
        ".js",
        ".html",
        ".css",
        ".txt",
    ]  # Add any other file extensions you want to include

    # Define files and directories to ignore
    ignore_files = [
        "__init__.py",
        "README.md",
        "LICENSE",
    ]
    ignore_dirs = [
        ".git",
        "__pycache__",
        "node_modules",
        ".venv",
        ".idea",
    ]

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Process code files for LLM input.')
    parser.add_argument('--all', action='store_true', help='Include all files.')
    parser.add_argument('--python', action='store_true', help='Include all Python files.')
    parser.add_argument('--folder', type=str, help='Filter by folder relative to root directory.')
    parser.add_argument('--backend', action='store_true', help='Include back-end files.')
    parser.add_argument('--frontend', action='store_true', help='Include front-end files.')
    parser.add_argument('--files', nargs='*', help='Specific files to include (relative to root directory).')
    args = parser.parse_args()

    # List all files in the directory, filtering out ignored files and directories
    all_files_list = list_files(root_directory, extensions, ignore_files, ignore_dirs)

    selected_files = set()

    if args.all:
        selected_files.update(all_files_list)
    if args.python:
        selected_files.update(f for f in all_files_list if f.endswith(".py"))
    if args.folder:
        folder_path = os.path.join(root_directory, args.folder)
        selected_files.update(f for f in all_files_list if os.path.commonpath([folder_path, f]) == folder_path)
    if args.backend:
        selected_files.update(filter_by_service(all_files_list, "Back-End"))
    if args.frontend:
        selected_files.update(filter_by_service(all_files_list, "Front-End"))
    if args.files:
        # Assume files are specified relative to root_directory
        selected_files.update(os.path.join(root_directory, f) for f in args.files)

    if not selected_files:
        print("No files selected. Exiting...")
        exit()

    selected_files = list(selected_files)

    # Save and display the selected files
    save_code_to_text(selected_files, output_file)
    print(f"Code saved to {output_file}")
    print("\nDisplaying full code content:\n")
    for file in selected_files:
        print(f"### File: {file} ###\n")
        try:
            with open(file, "r", encoding="utf-8") as f:
                print(f.read())
        except Exception as e:
            print(f"Could not read file {file}: {e}")
        print("\n" + "#" * 40 + "\n")

if __name__ == "__main__":
    main()
