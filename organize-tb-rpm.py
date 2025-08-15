#!/usr/bin/env python3

import os
import shutil
import argparse
import re
from collections import defaultdict

def extract_prefix(filename):
    """
    Extracts the 'WORD' prefix from a filename following the specified pattern.
    e.g., 'package-name-7.4.25-1.something.rpm' -> 'package-name'
    """
    # Regex to capture the prefix part.
    # The pattern looks for words (starting with a letter) separated by - or _,
    # followed by a dash and then a version number.
    match = re.search(r'([a-zA-Z][a-zA-Z0-9_\-]+)-\d', filename)
    if match:
        # The captured group is the prefix we're looking for.
        return match.group(1)
    return None

def process_directories(args):
    """
    Core function to process files in the target directory, find corresponding
    files in the source directory, and move them to their correct subdirectories.
    """
    source_dir = args.source
    target_dir = args.target
    do_move = args.action is not None
    verbose = args.verbose
    block_width = args.block_width
    line_width = args.line_width
    extension = args.extension
  
    # 1. Collect unique prefixes from the target directory and map them to
    #    the subdirectory they were found in.
    print('Processing target directory...')
    prefix_to_target_subdir = {}
    for root, _, files in os.walk(target_dir):
        for filename in files:
            if filename.endswith(extension):
                prefix = extract_prefix(filename)
                if prefix and prefix not in prefix_to_target_subdir:
                    prefix_to_target_subdir[prefix] = root

    if not prefix_to_target_subdir:
        print('No RPM files with valid prefixes found in the target directory.')
        return

    # Sort prefixes by length in descending order to handle longest names first
    sorted_prefixes = sorted(list(prefix_to_target_subdir.keys()), key=len, reverse=True)

    # 2. Collect files from the source directory, organized by their prefix
    print('Processing source directory...')
    source_files_by_prefix = defaultdict(list)
    for root, _, files in os.walk(source_dir):
        for filename in files:
            if filename.endswith('.rpm'):
                prefix = extract_prefix(filename)
                if prefix:
                    source_files_by_prefix[prefix].append(os.path.join(root, filename))

    # 3. Iterate through sorted prefixes, find matches, and perform actions
    print('Matching and moving files...')
    progress_counter = 0
    
    for prefix in sorted_prefixes:
        # Get the specific target subdirectory for this prefix
        target_subdir = prefix_to_target_subdir[prefix]
        
        if prefix in source_files_by_prefix:
            # Files found for the current prefix
            for source_path in source_files_by_prefix[prefix]:
                filename = os.path.basename(source_path)
                target_path = os.path.join(target_subdir, filename)
                
                # Check for dry run
                is_overwriting = os.path.exists(target_path)

                if do_move:
                    try:
                        shutil.move(source_path, target_path)
                    except Exception as e:
                        print(f'Error moving {filename}: {e}')
                        # Continue to the next file if there's an error
                        continue
                
                # Handle output based on verbose flag
                if verbose:
                    suffix = '!' if is_overwriting else ''
                    print(f'{filename} -> {target_subdir}{suffix}')
                else:
                    symbol = '!' if is_overwriting else '+'
                    print(symbol, end='', flush=True)
                    progress_counter += 1
                    if progress_counter % block_width == 0:
                        print(' ', end='', flush=True)
                    if progress_counter % line_width == 0:
                        print('')

            # Clear the entry for this prefix to avoid processing duplicates
            del source_files_by_prefix[prefix]
        else:
            # No files found for the current prefix
            if verbose:
                print(f'{prefix} skipped')
            else:
                print('.', end='', flush=True)
                progress_counter += 1
                if progress_counter % block_width == 0:
                    print(' ', end='', flush=True)
                if progress_counter % line_width == 0:
                    print('')
    
    # Final newline for non-verbose mode
    if not verbose and progress_counter > 0:
        print('\nDone.')

def main():
    """
    Main function to set up argument parsing and call the core logic.
    """
    parser = argparse.ArgumentParser(description="Move RPM files based on prefixes.")
    parser.add_argument('-i', '--source', required=True, help='Source directory to search for files.')
    parser.add_argument('-o', '--target', required=True, help='Target directory where prefixes are found and files will be moved.')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output.')
    parser.add_argument('action', nargs='?', choices=['do', 'DO', 'move', 'MOVE'],
                        help="Perform the move operation. If not provided, it's a dry run.")
    parser.add_argument('--block-width', type=int, default=10, help=argparse.SUPPRESS)
    parser.add_argument('--line-width', type=int, default=100, help=argparse.SUPPRESS)
    parser.add_argument('--extension', type=str, default='.rpm', help=argparse.SUPPRESS)

    args = parser.parse_args()

    # Determine if it's a dry run or an actual move
    do_move = args.action is not None

    # Validate that source and target directories exist
    if not os.path.isdir(args.source):
        parser.error(f'Source directory does not exist: {args.source}')
    if not os.path.isdir(args.target):
        parser.error(f'Target directory does not exist: {args.target}')

    print(f"Executing {'dry run' if not do_move else 'move'} from {args.source} to {args.target}")
    process_directories(args)
    
if __name__ == '__main__':
    main()