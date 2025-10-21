Vault - File Decryption Tool
A powerful Python tool for decrypting XOR-encrypted files with multiple operation modes and folder support.

🌟 Features
Multiple Operation Modes:

Automatic key detection

Manual brute-force decryption

Known key decryption

Folder Support: Process entire folders of encrypted files

File Type Detection: Automatically detects common file formats

Cross-Platform: Works on Windows, macOS, and Linux

User-Friendly: Interactive menu system with clear prompts

📋 Supported File Types
The tool can detect and decrypt various file formats including:

PNG images (\x89PNG\r\n\x1a\n)

JPEG images (\xff\xd8\xff\xe0, \xff\xd8\xff\xe1, \xff\xd8\xff\xe8)

MP4 videos (\x00\x00\x00\x18ftyp3gp)

PDF documents (%PDF)

ZIP archives (PK\x03\x04)

RAR archives (Rar!\x1a\x07)

🚀 Installation
Clone the repository:

bash
git clone 
cd to file
Requirements:

Python 3.6 or higher

No external dependencies required

🎯 Usage
Run the script:

bash
python 
Main Menu Options:
1. "I don't know the key" - Unknown Key Mode
Single File: Decrypt one file with automatic detection or brute-force

Entire Folder: Process all files in a folder with three methods:

Automatic detection: Tries to detect key and file type for each file

Manual mode: Tests all 256 possible keys for each file

Same key: Uses one key for all files (with auto-detection)

2. "I know the key" - Known Key Mode
Single File: Decrypt one file with a known key

Entire Folder: Decrypt all files in a folder using the same key

3. "About the program" - Program Information
🔧 How It Works
The tool uses XOR encryption/decryption on the first 128 bytes of files:

python
# XOR operation on first 128 bytes
for i, b in enumerate(data):
    if i < 128:
        new_data.append(b ^ key)  # XOR operation
    else:
        new_data.append(b)        # Keep original data
📁 Folder Processing
When processing folders:

Creates an output folder for decrypted files

Preserves original filenames with prefixes

Provides detailed success/failure reports

Supports batch operations for efficiency

🛠️ Technical Details
Encryption Method: XOR cipher on first 128 bytes

Key Range: 0-255 (1 byte)

Supported Platforms: Windows, Linux, macOS

File Signatures: Detects 7+ common file formats

📝 Usage Examples
Example 1: Decrypt Single File with Unknown Key
text
Choose an option:
1. I don't know the key
2. I know the key

Select: 1
1. Process single file
2. Process entire folder
Select: 1
1. Automatic detection
2. Manual mode
Example 2: Decrypt Entire Folder
text
Select: 1
1. Process single file
2. Process entire folder
Select: 2

Enter folder path: /path/to/encrypted/files
Enter output folder name: decrypted_files

1. Automatic detection for all files
2. Manual mode for all files
3. Use same key for all files
⚠️ Limitations
Only decrypts XOR encryption on first 128 bytes

Key must be between 0-255

File detection relies on known signatures

Large folders may take significant time in manual mode

🤝 Contributing
Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

🆘 Troubleshooting
File not found error: Ensure the file path is correct and accessible

Automatic detection failed: Try manual mode or verify the file is XOR encrypted

Operation failed: Check file permissions and available disk space

Folder processing slow: Manual mode tests 256 keys per file - use automatic mode for faster processing

📞 Support
For support and questions:

Open an issue on GitHub

Check the troubleshooting section above

Note: This tool is intended for legitimate decryption purposes only. Ensure you have the right to decrypt any files you process.
