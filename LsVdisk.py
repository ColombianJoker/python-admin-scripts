#!/usr/bin/env python3

import sys
import argparse
import textwrap
import subprocess
from typing import List, Dict

def run_ssh_command(ssh_host: str = None, command: str = None) -> str:
    """
    Executes a command on a remote host using the ssh command-line tool.
    Returns the stdout as a string. Raises an exception on failure.
    """
    try:
        result = subprocess.run(
            ['ssh', ssh_host, command],
            capture_output=True,
            text=True,
            check=True
        )
        # sys.stderr.write(f'\nDEBUG: {result.stdout.strip()=} {"-"*40}\n')
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"Error executing command on '{ssh_host}':\n")
        sys.stderr.write(f"Command: {e.cmd}\n")
        sys.stderr.write(f"Return code: {e.returncode}\n")
        sys.stderr.write(f"Stdout:\n{e.stdout}\n")
        sys.stderr.write(f"Stderr:\n{e.stderr}\n")
        sys.exit(1)
    except FileNotFoundError:
        sys.stderr.write("Error: The 'ssh' command-line tool was not found. Please ensure it is in your PATH.\n")
        sys.exit(1)

def parse_lsvdisk_table(output: str = None, delimiter: str = ':')-> List[Dict[str, str]]:
    """
    Parses a delimited table output from the lsvdisk command.
    Returns a list of dictionaries, one for each vdisk.
    """
    lines = output.splitlines()
    if not lines or 'id' not in lines[0]:
        raise ValueError("Invalid lsvdisk output format. Missing header or 'id'.")

    header = lines[0].strip().split(delimiter)
    volumes = []
    
    for line in lines[1:]:
        if not line.strip():
            continue
        
        parts = line.strip().split(delimiter)
        if len(parts) == len(header):
            volume_data = {header[i]: parts[i].strip() for i in range(len(header))}
            volumes.append(volume_data)
    # sys.stderr.write(f'\DEBUG: {volumes[:2]=} {"-"*40}\n')
    return volumes

def main() -> None:
    parser = argparse.ArgumentParser(
        description="List and filter vdisks from a Spectrum Virtualize host.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''\
            Example usage:
              ./LsVdisk.py -d ':' svchost.example.com WTIERA1
              ./LsVdisk.py -p -u svchost.example.com 'products'
        ''')
    )
    parser.add_argument('ssh_host', help="The name of the SSH host defined in ~/.ssh/config.")
    parser.add_argument('search_string', help="A partial, case-insensitive string to match against vdisk names.")
    parser.add_argument('-p', '--pool', action='store_true', help="Show the storage pool name.")
    parser.add_argument('-g', '--group', action='store_true', help="Show the volume group name.")
    parser.add_argument('-u', '--uuid', action='store_true', help="Show the vdisk UID.")
    parser.add_argument('-d', '--delimiter', default=':', help="The delimiter character to use for parsing the command output.")
    args = parser.parse_args()

    # Get list of all volumes from lsvdisk
    lsvdisk_cmd = f"lsvdisk -bytes -delim {args.delimiter}"
    lsvdisk_output = run_ssh_command(args.ssh_host, lsvdisk_cmd)
    
    try:
        all_vdisks = parse_lsvdisk_table(lsvdisk_output, args.delimiter)
    except ValueError as e:
        sys.stderr.write(f"Error parsing lsvdisk output: {e}\n")
        sys.exit(1)

    # Filter vdisks by the search string
    filtered_vdisks = [
        vdisk for vdisk in all_vdisks 
        if args.search_string.lower() in vdisk.get('name', '').lower()
    ]

    # Prepare header with fixed-width columns
    header = ' ID VDISK                             SIZE GB'
    if args.pool:
        header += ' POOL            '
    if args.group:
        header += ' GROUP           '
    if args.uuid:
        header += ' VUID                             '
    
    sys.stdout.write(header + '\n')
    
    # Process each filtered volume
    for vdisk_data in filtered_vdisks:
        vol_id = vdisk_data.get('id', '')
        vol_name = vdisk_data.get('name', '')
        
        try:
            # Capacity is already in bytes thanks to the -bytes flag
            capacity_bytes = int(vdisk_data.get('capacity', 0))
            capacity_gb = capacity_bytes / (1024**3)
            
            output_line = f"{vol_id:>3} {vol_name:<32} {capacity_gb:>8.2f}"

            if args.pool:
                pool_name = vdisk_data.get('mdisk_grp_name', '')
                output_line += f" {pool_name:<16}"
            if args.group:
                group_name = vdisk_data.get('volume_group_name', '')
                output_line += f" {group_name:<16}"
            if args.uuid:
                uuid = vdisk_data.get('vdisk_UID', '')
                output_line += f" {uuid:<33}"

            sys.stdout.write(output_line + '\n')

        except Exception as e:
            sys.stderr.write(f"Error processing volume '{vol_name}': {e}\n")
            continue

if __name__ == "__main__":
    main()