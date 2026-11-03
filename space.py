####################################################################
# SPACE CHECKER
# Created by crazykiddo (crazykiddo.net)
# https://github.com/crazykiddo/space
# Version 1.2
####################################################################
# CHANGES
# - External host list setup
#
#
import warnings
warnings.simplefilter('ignore')

import os
import shutil
import socket
import paramiko
import json

# List of hosts to check
from pathlib import Path
HOSTS_FILE = Path(__file__).resolve().with_name("space.json")
with HOSTS_FILE.open(encoding="utf-8") as file:
    hosts = json.load(file)
   
# Config
showfull = False  # Show full disk space details

def check_disk_space(host):
    hostname = host["hostname"]
    username = host["username"]
    hosttype = host["hosttype"]
    hosttitle = host["hosttitle"]
    # mainvol = host["mainvol"]
    # if not mainvol:
    #   mainvol = "/"
    port = host["port"]
    if not port:
        port = 22  # Default SSH port if not specified
    password = host.get("password")
    key_filename = host.get("key_filename")
    totalfree_space = 0
    # print(f"-----------------------------------\n")
    if showfull:
        print(f"\n Connecting to {hostname}...")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Check if host is localhost
    if hostname in ["localhost", "127.0.0.1"]:
        # Local disk space check
        if os.name == "nt":
            # Windows: check all drives
            import string

            drives = [
                f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")
            ]
            total_free = 0
            for drive in drives:
                usage = shutil.disk_usage(drive)
                free_mb = usage.free / (1024 * 1024)
                total_free += free_mb
                if showfull:
                    print(
                        f"  {drive}: Size {usage.total / 1024 / 1024 / 1024:.2f} GB, Free {free_mb / 1024:.2f} GB"
                    )
            totalfree_space = total_free
            if total_free > 1024:
                print(f" [{hosttitle}] Free Space: {total_free / 1024:.2f} GB")
            else:
                print(f" [{hosttitle}] Free Space: {total_free:.2f} MB")
        else:
            # Linux/macOS: check root
            usage = shutil.disk_usage("/")
            free_mb = usage.free / (1024 * 1024)
            totalfree_space = free_mb
            if showfull:
                print(
                    f"  /: Size {usage.total / 1024 / 1024 / 1024:.2f} GB, Free {free_mb / 1024:.2f} GB"
                )
            if free_mb > 1024:
                print(f" [{hosttitle}] Free Space: {free_mb / 1024:.2f} GB")
            else:
                print(f" [{hosttitle}] Free Space: {free_mb:.2f} MB")
        print(f"-------------------------------------------------------")
        return totalfree_space
    else:
        WHITE = '\033[37m'
        GRAY = '\033[90m'
        try:
            connect_kwargs = dict(
                username=username,
                password=password,
                key_filename=key_filename,
                timeout=5,
                port=port,
            )
            if host.get("legacy_ssh_rsa"):
                # connect_kwargs["disabled_algorithms"] = dict(pubkeys=["rsa-sha2-256", "rsa-sha2-512"])
                connect_kwargs["look_for_keys"] = False
                connect_kwargs["allow_agent"] = False
            
            client.connect(hostname, **connect_kwargs)

            # Detect OS type by checking for 'ver' (Windows) or fallback to Linux
            stdin, stdout, stderr = client.exec_command("ver")
            output = stdout.read().decode().lower()
            is_windows = "windows" in output
            if is_windows:
                # print(f"[{hostname}] Detected Windows.")
                command = (
                    "wmic logicaldisk where DriveType=3 get DeviceID,FreeSpace,Size"
                )
            else:
                # print(f"[{hostname}] Detected Linux.")
                command = "/bin/df -h --output=source,size,used,avail,pcent,target || df -h --output=source,size,used,avail,pcent,target"

            stdin, stdout, stderr = client.exec_command(command)
            result = stdout.read().decode().strip()
            error = stderr.read().decode().strip()

            if result:
                if not is_windows:
                    # Linux: print each filesystem and sum available space
                    lines = result.splitlines()
                    total_avail = 0
                    if showfull:
                        print(f" [{hosttitle}] Free Space:")
                    for line in lines[1:]:  # Skip header
                        parts = line.split()
                        if len(parts) < 6:
                            continue
                        fs, size, used, avail, pcent, mount = parts[:6]
                        # Convert avail to MB
                        if avail.endswith("G"):
                            avail_mb = float(avail[:-1]) * 1024
                        elif avail.endswith("M"):
                            avail_mb = float(avail[:-1])
                        elif avail.endswith("K"):
                            avail_mb = float(avail[:-1]) / 1024
                        else:
                            try:
                                avail_mb = float(avail) / (1024 * 1024)
                            except ValueError:
                                continue
                        total_avail += avail_mb
                        if avail_mb > 1024:
                            avail_str = f"{avail_mb / 1024:.2f} GB"
                        else:
                            avail_str = f"{avail_mb:.2f} MB"
                        if showfull:
                            print(f"  {mount}: Size {size}, Free {avail_str}")
                        totalfree_space = total_avail  # <-- only sum for this host
                    if total_avail > 1024:
                        print(f" [{hosttitle}] Free Space: {total_avail / 1024:.2f} GB")
                    else:
                        print(f" [{hosttitle}] Free Space: {total_avail:.2f} MB")
                else:
                    # Windows: print each drive and sum free space
                    lines = result.splitlines()
                    total_free = 0
                    if showfull:
                        print(f" [{hostname}] Free Space:")
                    for line in lines[1:]:  # Skip header
                        parts = line.split()
                        if len(parts) < 3:
                            continue
                        device, free, size = parts[:3]
                        try:
                            free_bytes = float(free)
                            size_bytes = float(size)
                            free_mb = free_bytes / (1024 * 1024)
                            size_mb = size_bytes / (1024 * 1024)
                            total_free += free_mb
                            if free_mb > 1024:
                                free_str = f"{free_mb / 1024:.2f} GB"
                            else:
                                free_str = f"{free_mb:.2f} MB"
                            if size_mb > 1024:
                                size_str = f"{size_mb / 1024:.2f} GB"
                            else:
                                size_str = f"{size_mb:.2f} MB"
                            if showfull:
                                print(f"  {device}: Size {size_str}, Free {free_str}")
                        except ValueError:
                            continue
                    totalfree_space = total_free  # <-- only sum for this host
                    if total_free > 1024:
                        print(f" [{hosttitle}] Free Space: {total_free / 1024:.2f} GB")
                    else:
                        print(f" [{hosttitle}] Free Space: {total_free:.2f} MB")
            else:
                print(f" [{hostname}] Disk Info is empty.")
                if error:
                    print(f" [{hostname}] Error output:\n{error}")

        except (paramiko.ssh_exception.SSHException, socket.error) as e:
            # print(f" [{hostname}] Connection failed: {e}")
            # print(f"{RED}This is red text!{RESET}")
            # print(f"{GRAY} [{hosttitle}] N/A{WHITE}")
            print(f" [{hosttitle}] N/A")
        finally:
            print(f"-------------------------------------------------------")
            client.close()
        return totalfree_space  # <-- return only this host's free space


def main():
    print(f"#######################################################")
    print(f" SPACE CHECKER")
    print(f"#######################################################")
    totalfree_space = 0  # <-- local to main
    for host in hosts:
        totalfree_space += check_disk_space(host)  # <-- sum each host's free space
    # Show total free space for all hosts
    print(f"#######################################################")
    if totalfree_space > 1024:
        print(f" TOTAL FREE SPACE: {totalfree_space / 1024:.2f} GB")
    else:
        print(f" TOTAL FREE SPACE: {totalfree_space:.2f} MB")
    print(f"#######################################################")


if __name__ == "__main__":
    main()
