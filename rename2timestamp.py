#!/usr/bin/env python3.11
#
import argparse
import os
import re
import time


def rename_file(filename, timestamp_type, format_string, debug_mode):
    """
    Renames a single file by replacing its embedded date/time string with
    the file's metadata timestamp (created, modified, or accessed).
    """

    # --- 1. Define the Universal Regular Expression Pattern ---
    # This pattern matches either the PDF Expert or Firefox date/time string
    # and captures the prefix ($1), the suffix ($5), and the part to be replaced ($2-$4).
    #
    # Pattern explanation:
    # ^(.*?)             # $1: Prefix (non-greedy)
    # (\d{4}-\d{2}-\d{2}) # $2: Date (YYYY-mm-dd)
    # \s+                 # Whitespace separator
    # (at)?               # $3: Optional 'at' (for PDF Expert)
    # \s?                 # Optional space
    # (\d{2}[_.]\d{2}[_.]\d{2}) # $4: Time (with . or _)
    # \s? ?               # Optional space/non-breaking space
    # ([AP]M)?            # $5: Optional AM/PM
    # (.*?)               # $6: Suffix (non-greedy, including any leading space)
    # $                   # End of the name (before the extension)

    # Note: We match against the name *without* the extension.
    # The RegEx is adapted slightly to handle Python's re syntax cleanly.
    pattern = re.compile(
        r"^(.*?)(\d{4}-\d{2}-\d{2})\s+(at)?\s?(\d{2}[_.]\d{2}[_.]\d{2})([\s\u202f]?)([AP]M)?(.*?)$",
        re.VERBOSE | re.IGNORECASE,
    )

    # --- 2. Separate Name and Extension ---
    base_name, file_extension = os.path.splitext(filename)

    # --- 3. Get the File Statistics ---
    try:
        stats = os.stat(filename)
    except FileNotFoundError:
        print(f"Error: File not found: {filename}")
        return

    # --- 4. Select the Correct Timestamp ---
    if timestamp_type == "M":
        timestamp_sec = stats.st_mtime  # Modified time
    elif timestamp_type == "A":
        timestamp_sec = stats.st_atime  # Accessed time
    else:  # Default is 'C' (created)
        timestamp_sec = stats.st_birthtime

    # Convert timestamp to the desired string format
    new_timestamp_str = time.strftime(format_string, time.localtime(timestamp_sec))

    if debug_mode:
        print(f"\n--- DEBUG: {filename} ---")
        print(f"Base Name: '{base_name}'")
        print(f"Extension: '{file_extension}'")
        print(f"Using Timestamp ({timestamp_type}): {new_timestamp_str}")
        print(f"Format String: {format_string}")

    # --- 5. Apply the RegEx and Build the New Name ---
    match = pattern.match(base_name)

    if match:
        prefix = match.group(1).strip()  # $1: Prefix
        suffix = match.group(6).strip()  # $6: Suffix

        # Build the new name: Prefix + New Timestamp + Suffix + Extension
        # Note: We put a single space between parts, and skip if a part is empty.
        new_name_parts = [prefix]
        new_name_parts.append(new_timestamp_str)
        if suffix:
            new_name_parts.append(suffix)

        new_base_name = " ".join(part for part in new_name_parts if part)
        new_filename = new_base_name + file_extension

        if debug_mode:
            print(f"RegEx Matched! Prefix: '{prefix}', Suffix: '{suffix}'")
            print(f"New Filename: '{new_filename}'")

        if filename != new_filename:
            try:
                if not debug_mode:
                    os.rename(filename, new_filename)
                print(f"Renamed: '{filename}' -> '{new_filename}'")
            except OSError as e:
                print(f"Error renaming {filename}: {e}")
        else:
            print(f"Skipped: Filename already correct: {filename}")

    else:
        print(f"Skipped: No date/time pattern found in name: {filename}")


def main():
    parser = argparse.ArgumentParser(
        description="Rename files by replacing an embedded date/time string with a file metadata timestamp.",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "filenames", nargs="+", help="One or more filenames to process."
    )

    parser.add_argument(
        "--DEBUG",
        action="store_true",
        help="Run in debug mode (shows matches and new name, but does NOT rename).",
    )

    parser.add_argument(
        "-F",
        "--format",
        dest="format_string",
        default="%Y-%m-%d %H.%M.%S",
        help='Timestamp format string (strftime). Default: "%%Y-%%m-%%d %%H.%%M.%%S"',
    )

    parser.add_argument(
        "-t",
        "--timestamp",
        dest="timestamp_type",
        default="C",
        choices=["M", "C", "A", "modified", "created", "accessed"],
        help="Type of file timestamp to use for renaming:\n"
        "  M/modified: Modification Time\n"
        "  C/created: Creation Time (default)\n"
        "  A/accessed: Access Time",
    )

    args = parser.parse_args()

    # Normalize timestamp input
    if args.timestamp_type in ["modified"]:
        args.timestamp_type = "M"
    elif args.timestamp_type in ["accessed"]:
        args.timestamp_type = "A"
    elif args.timestamp_type in ["created"]:
        args.timestamp_type = "C"

    for filename in args.filenames:
        rename_file(filename, args.timestamp_type, args.format_string, args.DEBUG)


if __name__ == "__main__":
    main()
