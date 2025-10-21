#!/usr/bin/env python3
"""
Vault-Blaster (Python) - Full-featured, non-destructive
Features:
 - Process a single file or a whole folder (recursive).
 - Mode A: You know the key -> apply XOR on the ENTIRE file and write output (original kept).
 - Mode B: You don't know key -> automatic mode:
           * try keys 0..255 by XORing HEAD_BYTES and checking signatures,
           * if match -> apply XOR on ENTIRE file with that key and write recovered file.
 - Mode C: Brute force all keys and write outputs (optional; can produce many files).
 - Does NOT delete or overwrite originals. Writes to OUT_FOLDER.
"""
import os
import sys
from pathlib import Path
from tkinter import Tk
from tkinter.filedialog import askdirectory, askopenfilename
import time

# ---------- Config ----------
OUT_FOLDER = "vault_recovered_output"
HEAD_BYTES = 64  # عند الفحص التجريبي للمفتاح نقرأ هذه البايتات
# ---------- Signatures for detection ----------
SIGNATURES = {
    ".jpg": [b'\xff\xd8\xff'],
    ".png": [b'\x89PNG\r\n\x1a\n'],
    ".gif": [b'GIF87a', b'GIF89a'],
    ".bmp": [b'BM'],
    ".webp": [b'RIFF'],   # requires offset 8..12 == b'WEBP'
    ".mp4": [b'\x00\x00\x00'],  # check for 'ftyp' later
    ".mkv": [b'\x1A\x45\xDF\xA3'],
    ".avi": [b'RIFF'],
    ".svg": [b'<?xml '],
    ".wmv": [b'\x30\x26\xB2\x75'],
    ".mpg": [b'\x00\x00\x01\xBA'],
}

# ---------- Helpers ----------
def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def choose_file_gui():
    Tk().withdraw()
    p = askopenfilename(title="Select file to process")
    return Path(p) if p else None

def choose_folder_gui():
    Tk().withdraw()
    d = askdirectory(title="Select folder to process")
    return Path(d) if d else None

def looks_like_format(head: bytes) -> str:
    """Return extension string if head matches known signature, else ''."""
    if len(head) >= 12:
        if head[0:4] == b'RIFF' and head[8:12] == b'WEBP':
            return ".webp"
        if head[0:4] == b'RIFF' and head[8:12] in (b'AVI ', b'AVIF', b'AV1 '):
            return ".avi"
    if b'ftyp' in head[:32]:
        return ".mp4"
    for ext, sigs in SIGNATURES.items():
        for sig in sigs:
            if head.startswith(sig):
                return ext
    return ""

def xor_stream(in_path: Path, out_path: Path, key: int, apply_on_full=True, limit_bytes=128):
    """Stream XOR from in_path to out_path.
       - if apply_on_full True -> XOR entire file with key
       - else XOR only first limit_bytes bytes then copy rest unchanged
    """
    CHUNK = 65536
    try:
        with open(in_path, 'rb') as fr, open(out_path, 'wb') as fw:
            remaining_limit = limit_bytes if not apply_on_full else None
            while True:
                chunk = fr.read(CHUNK)
                if not chunk:
                    break
                if apply_on_full:
                    proc = bytes(b ^ key for b in chunk)
                    fw.write(proc)
                else:
                    if remaining_limit is None:
                        fw.write(chunk)
                    elif remaining_limit <= 0:
                        fw.write(chunk)
                    else:
                        # need to XOR first part of this chunk
                        n = min(len(chunk), remaining_limit)
                        proc = bytearray(chunk)  # mutable
                        for i in range(n):
                            proc[i] ^= key
                        fw.write(proc)
                        remaining_limit -= n
        return True
    except Exception as e:
        print(f"    [ERROR] Writing {out_path}: {e}")
        return False

def try_keys_on_head(path: Path, head_bytes=HEAD_BYTES):
    """Try keys 0..255 on the HEAD and return list of (key, ext) candidates."""
    try:
        with open(path, 'rb') as f:
            head = f.read(head_bytes)
    except Exception as e:
        print(f"[SKIP] Cannot read {path}: {e}")
        return []
    candidates = []
    for k in range(256):
        xhead = bytes(b ^ k for b in head)
        ext = looks_like_format(xhead)
        if ext:
            # extra checks
            if ext == ".webp" and (len(xhead) < 12 or xhead[8:12] != b'WEBP'):
                continue
            candidates.append((k, ext))
    return candidates

# ---------- High-level operations ----------
def recover_with_known_key(path: Path, key:int, out_dir: Path, apply_on_full=True):
    """Apply XOR with known key and write file. Returns output path or None."""
    out_name = f"{path.stem}_recovered_k{key:03d}{path.suffix}"
    out_path = out_dir / out_name
    ok = xor_stream(path, out_path, key, apply_on_full)
    return out_path if ok else None

def auto_recover_file(path: Path, out_dir: Path, apply_on_full=True):
    """Try keys 0..255 by header detection; when candidate found, write full XOR file.
       Returns number of written files for this input."""
    written = 0
    candidates = try_keys_on_head(path)
    if not candidates:
        return 0
    for key, ext in candidates:
        out_name = f"{path.stem}_recovered_k{key:03d}{ext}"
        out_path = out_dir / out_name
        print(f"  [FOUND] {path.name} -> key={key}, ext={ext} -> writing {out_name}")
        ok = xor_stream(path, out_path, key, apply_on_full)
        if ok:
            written += 1
    return written

def brute_all_keys_write(path: Path, out_dir: Path, fext):
    """Write outputs for all 256 keys using fext (dangerous: many files)."""
    written = 0
    for k in range(256):
        out_name = f"{path.stem}_KEY{k:03d}{fext}"
        out_path = out_dir / out_name
        ok = xor_stream(path, out_path, k, apply_on_full=True)
        if ok:
            written += 1
    return written

# ---------- Batch processing ----------
def process_single_file(path: Path, out_dir: Path, mode:str, apply_on_full=True):
    """mode: 'known', 'auto', 'brute'"""
    print(f"Processing file: {path}")
    out_dir.mkdir(parents=True, exist_ok=True)
    if mode == 'known':
        k = input("Enter key (0-255): ")
        try:
            key = int(k)
            if not (0 <= key <= 255):
                raise ValueError()
        except ValueError:
            print("Invalid key.")
            return
        # ask extension if user wants to change extension in output
        ext = input("Enter extension to use for output file (with .) or press Enter to keep original suffix: ").strip()
        if ext:
            out_name = f"{path.stem}_recovered_k{key:03d}{ext}"
            out_path = out_dir / out_name
            ok = xor_stream(path, out_path, key, apply_on_full)
            print("Wrote" if ok else "Failed to write", out_path)
        else:
            out_path = out_dir / f"{path.stem}_recovered_k{key:03d}{path.suffix}"
            ok = xor_stream(path, out_path, key, apply_on_full)
            print("Wrote" if ok else "Failed to write", out_path)

    elif mode == 'auto':
        written = auto_recover_file(path, out_dir, apply_on_full)
        if written == 0:
            print(f"  -> No candidate key found for {path.name}")
        else:
            print(f"  -> Wrote {written} recovered file(s) for {path.name}")

    elif mode == 'brute':
        fext = input("Enter extension to give the brute-forced files (with .): ").strip()
        if not fext:
            fext = path.suffix
        written = brute_all_keys_write(path, out_dir, fext)
        print(f"  -> Wrote {written} files (brute) for {path.name}")

def process_folder(folder: Path, out_dir: Path, mode:str, apply_on_full=True):
    print(f"Scanning folder: {folder} (mode={mode}, apply_on_full={apply_on_full})")
    files = [p for p in folder.rglob("*") if p.is_file()]
    print(f"Found {len(files)} files. Processing...")
    total_written = 0
    for idx, f in enumerate(files, 1):
        print(f"\n[{idx}/{len(files)}] {f.relative_to(folder)}")
        if mode == 'known':
            # user provides single key applied to all files
            k = input("Enter key to apply to all files (0-255): ")
            try:
                key = int(k); assert 0 <= key <= 255
            except:
                print("Invalid key, skipping file.")
                continue
            out_name = f"{f.stem}_recovered_k{key:03d}{f.suffix}"
            out_path = out_dir / out_name
            ok = xor_stream(f, out_path, key, apply_on_full)
            if ok: total_written += 1
        else:
            # for 'auto' and 'brute', call per-file logic
            if mode == 'auto':
                written = auto_recover_file(f, out_dir, apply_on_full)
                total_written += written
            elif mode == 'brute':
                # ask per folder once?
                ext = input("Enter extension to give brute outputs (with .): ").strip()
                written = brute_all_keys_write(f, out_dir, ext or f.suffix)
                total_written += written
    print(f"\nDone. Total written: {total_written}. Output folder: {out_dir.resolve()}")

# ---------- CLI ----------
def main_menu():
    clear_console()
    print("Vault Blaster - Python (non-destructive)")
    print("IMPORTANT: This program will NOT delete originals. It writes recovered copies into a separate folder.")
    print()
    print("Select input type:")
    print(" 1) Single file (choose file)")
    print(" 2) Folder (choose folder) - recursive")
    choice = input("Choice: ").strip()
    if choice == '1':
        file_path = choose_file_gui()
        if not file_path:
            print("No file chosen. Exiting.")
            return
    elif choice == '2':
        file_path = choose_folder_gui()
        if not file_path:
            print("No folder chosen. Exiting.")
            return
    else:
        print("Invalid choice. Exiting.")
        return

    # choose mode
    print("\nMode:")
    print(" 1) I know the key (apply XOR with known key to entire file(s))")
    print(" 2) I don't know the key (auto detect by trying keys 0..255 on header)")
    print(" 3) Brute-force: write outputs for all keys (DANGEROUS; many files)")
    mode_choice = input("Mode (1/2/3): ").strip()
    mode_map = {'1':'known','2':'auto','3':'brute'}
    mode = mode_map.get(mode_choice)
    if not mode:
        print("Invalid mode. Exiting.")
        return

    # choose whether to apply XOR to full file or first N bytes (backward compatibility)
    ao = input("Apply XOR to full file? (Y=full / N=only first 128 bytes): ").strip().lower()
    apply_on_full = True if ao == 'y' or ao == 'yes' or ao == '' else False

    # output folder
    out_dir = Path(OUT_FOLDER)
    out_dir.mkdir(parents=True, exist_ok=True)

    if file_path.is_file():
        process_single_file(file_path, out_dir, mode, apply_on_full)
    else:
        process_folder(file_path, out_dir, mode, apply_on_full)

    print("\nAll done. Check output folder:", out_dir.resolve())

if __name__ == "__main__":
    main_menu()
