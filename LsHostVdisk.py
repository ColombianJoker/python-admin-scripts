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

def parse_lshost_output(output: str = None) -> Dict[str,str]:
    """
    Parses the key-value output of lshost and returns a dictionary.
    Collects multiple WWPNs into a list.
    """
    data = {}
    wwpns = []
    lines = output.splitlines()
    for line in lines:
        if 'WWPN' in line:
            wwpns.append(line.split()[1].strip())
        elif ' ' in line.strip():
            parts = line.split(' ', 1)
            key = parts[0].strip()
            value = parts[1].strip()
            if key and value:
                data[key] = value
    data['WWPNs'] = wwpns
    return data

def parse_delimited_table(output: str = None, delimiter: str = ':')-> List[Dict[str, str]]:
    """
    Parses a delimited table output from lshostvdiskmap or lsvdisk.
    Returns a list of dictionaries, one for each row.
    """
    lines = output.splitlines()
    if not lines or not lines[0]:
        return []
    header = lines[0].strip().split(delimiter)
    
    table_data = []
    for line in lines[1:]:
        if not line.strip():
            continue
        
        parts = line.strip().split(delimiter)
        if len(parts) == len(header):
            row_data = {header[i]: parts[i].strip() for i in range(len(header))}
            table_data.append(row_data)
    return table_data

def parse_delimited_kv_line(output: str = None, delimiter: str = ':')-> List[Dict[str, str]]:
    """
    Parses a multi-line, key-value output from a delimited command
    and returns a dictionary.
    """
    data = {}
    if not output:
        return data
        
    pairs = output.split('\n')
    for pair in pairs:
        if delimiter in pair:
            key, value = pair.split(delimiter, 1)
            data[key.strip()] = value.strip()
    return data

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Show information for a host definition on an IBM Spectrum Virtualize system.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''\
            Example usage:
              ./LsHostVdisk.py CRCCvpntriarafs5k WTIERA1
              ./LsHostVdisk.py -cw CRCCvpntriarafs5k WTIERA1
              ./LsHostVdisk.py -vsw CRCCvpntriarafs5k WTIERA1
        ''')
    )
    parser.add_argument('ssh_host', help="The name of the SSH host defined in ~/.ssh/config.")
    parser.add_argument('host_name', help="The host definition name in the Spectrum Virtualize system.")
    parser.add_argument('-c', '--cluster', action='store_true', help="Show the host cluster name.")
    parser.add_argument('-w', '--wwpn', action='store_true', help="Show a list of WWPNs for the host.")
    parser.add_argument('-v', '--vdisks', action='store_true', help="Show a list of mapped vdisks for the host.")
    parser.add_argument('-s', '--size', action='store_true', help="Show the size of the mapped vdisks (requires -v).")
    args = parser.parse_args()
    
    # 1. Get host info using lshost
    lshost_cmd = f"lshost {args.host_name}"
    lshost_output = run_ssh_command(args.ssh_host, lshost_cmd)
    host_data = parse_lshost_output(lshost_output)

    # 2. Build and print the basic host info line
    main_line = (f"{host_data.get('id'):<3} {host_data.get('name', ''):<18}"
                 f"{host_data.get('port_count', ''):>4} {host_data.get('status', ''):<8}")
    
    if args.cluster:
        cluster_name = host_data.get('host_cluster_name', '')
        main_line += f" {cluster_name}"
    
    if args.wwpn:
        wwpns_str = ":".join(host_data.get('WWPNs', []))
        main_line += f" {wwpns_str:>40}"
    
    sys.stdout.write(main_line + '\n')
    
    # 3. Handle the optional volume list if -v is specified
    if args.vdisks:
        sys.stdout.write('\n')
        
        # Get volume mappings using lshostvdiskmap
        lshostvdiskmap_cmd = f"lshostvdiskmap -delim : {args.host_name}"
        lshostvdiskmap_output = run_ssh_command(args.ssh_host, lshostvdiskmap_cmd)
        mapped_vdisks = parse_delimited_table(lshostvdiskmap_output, ':')

        # Build and print the volume list header to stderr with fixed widths
        header_line = f'{"ID":>3} {"#":>2} {"VDISK":<32}'
        if args.size:
            header_line += f' {"SIZE":>5}'
        header_line += f' {"VUID":<32}'
        sys.stderr.write(header_line + '\n')

        # Process each mapped volume
        for vol_map in mapped_vdisks:
            vol_id = vol_map.get('vdisk_id', '')
            vol_name = vol_map.get('vdisk_name', '')
            scsi_id = vol_map.get('SCSI_id', '')
            
            # Conditionally get the size if -s is specified
            capacity_gb_str = ''
            if args.size:
                lsvdisk_cmd = f"lsvdisk -bytes -delim : {vol_name}"
                lsvdisk_output = run_ssh_command(args.ssh_host, lsvdisk_cmd)
                vdisk_data = parse_delimited_kv_line(lsvdisk_output, ':')
                
                capacity_bytes = int(vdisk_data.get('capacity', 0))
                capacity_gb = capacity_bytes / (1024**3)
                capacity_gb_str = f"{int(capacity_gb):>5}"
            
            # Get VUID from the original lshostvdiskmap output
            vdisk_uid = vol_map.get('vdisk_UID', '')
            
            # Build and print the volume line with fixed widths
            volume_line = f"{vol_id:>3} {scsi_id:>2} {vol_name:<32}"
            if args.size:
                volume_line += f" {capacity_gb_str:>5}"
            volume_line += f" {vdisk_uid:<32}"

            sys.stdout.write(volume_line + '\n')

if __name__ == "__main__":
    main()