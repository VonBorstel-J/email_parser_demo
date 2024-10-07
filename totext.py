import os

def save_code_to_text(root_dir, output_file, extensions=None):
    if extensions is None:
        extensions = [".py", ".js", ".html", ".css", ".txt"]  # Add file extensions of the code you want to include.

    with open(output_file, 'w', encoding='utf-8') as f_out:  # Use UTF-8 encoding
        for foldername, subfolders, filenames in os.walk(root_dir):
            for filename in filenames:
                if any(filename.endswith(ext) for ext in extensions):
                    file_path = os.path.join(foldername, filename)
                    f_out.write(f"### File: {file_path} ###\n\n")  # Add header with filename
                    with open(file_path, 'r', encoding='utf-8') as f_in:
                        f_out.write(f_in.read())  # Write file content
                    f_out.write("\n\n" + "#" * 40 + "\n\n")  # Add a separator between files

if __name__ == "__main__":
    root_directory = r"C:\Users\jorda\OneDrive\Desktop\Code & Ai\email_parser_demo"  # Raw string to avoid escape issues
    output_file = "codebase.txt"  # Output file for LLM input
    save_code_to_text(root_directory, output_file)

    print(f"Code saved to {output_file}")
