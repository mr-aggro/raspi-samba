from smb.SMBConnection import SMBConnection
from smb.base import NotReadyError
import subprocess
import platform
import argparse
import sys


parser = argparse.ArgumentParser()
parser.add_argument('server',
                    help='Use server') # For netbios name
parser.add_argument('-np', '--nopswd',
                    help='Use without password',
                    action="store_true") # For login without password
parser.add_argument('-u', '--username',
                    help='Use alternate username',
                    default="guest") # For alternate usernames
parser.add_argument('-p', '--password',
                    help='Use alternate password',
                    default='') # For alternate passwords
parser.add_argument('-m', '--mount',
                    help='Mount point',
                    default=None) # For mount point
parser.add_argument('-v', '--volume',
                    help='SMB volume name for mount',
                    default=None) # For volume to mount
parser.add_argument('-L', '--list',
                    help='Show list of shares',
                    action="store_true") # For list of shares
args = parser.parse_args()
TICK="[\033[32m✓\033[0m]"
CROSS="[\033[31m✗\033[0m]"
user = args.username
password = args.password
client_machine_name = 'Linux'
server_name = args.server
server_ip = None
print("[i]OS: ", platform.system())
if platform.system() == 'Linux':
    fails = 0
	print(TICK+"Try to reslove ip for {}".format(server_name))
    while fails < 5:
        cmd = "nmblookup {} | cut -d \" \" -f1".format(server_name)
        server_ip = subprocess.check_output(cmd, shell=True, universal_newlines=True)
        if server_ip[:-1] == "name_query":
            fails += 1
            server_ip = "Error"
        else:
            break
if args.nopswd is True:
    smbcon = SMBConnection(user, "", "Linux", server_name)
else:
    smbcon = SMBConnection(user, password, "Linux", server_name)
try:
    if server_ip == "Error":
        print(CROSS+"Can't reslove IP. Abort.")
        sys.exit(1)
    elif server_ip is not None:
        print("[i]  Connect via IP {}".format(server_ip[:-1]))
        state = smbcon.connect(server_ip)
    else:
        print("[i]  Connect via NetBIOS")
        state = smbcon.connect(server_name)
    if state is True:
        arr = []
        for share in smbcon.listShares():
            if share.isSpecial is False:
                arr.append(share.name)
        if args.list is True:
            print("List of shares:")
            count = 1
            for share in arr:
                print("[{}] {}".format(count, share))
                count += 1
        smbcon.close()
    else:
        raise NotReadyError("SMB connection ERROR")
    if (args.mount is not None) and (args.volume is not None):
        if args.volume in arr:
            print("[i]Mounting volume {} at {}".format(args.volume, args.mount))
            if args.nopswd is True:
                cmd = "echo \'username={}\' > /tmp/smb".format(user)
                subprocess.check_output(cmd, shell=True)
                cmd = "echo \'password=\' >> /tmp/smb"
                subprocess.check_output(cmd, shell=True)
                cmd = "sudo mount.cifs //{}/{} {} -o credentials=/tmp/smb".format(server_ip[:-1], args.volume, args.mount)
                try:
                    out = subprocess.check_output(cmd, shell=True, universal_newlines=True)
                    cmd = "rm /tmp/smb"
                    subprocess.check_output(cmd, shell=True)
                    print(TICK + "\033[32mDone!\033[0m")
                except subprocess.CalledProcessError:
                    print(CROSS+"Error while execute mount")
            else:
                cmd = "echo \'username={}\' > /tmp/smb".format(user)
                subprocess.check_output(cmd, shell=True)
                cmd = "echo \'password={}\' >> /tmp/smb".format(password)
                subprocess.check_output(cmd, shell=True)
                cmd = "sudo mount.cifs //{}/{} {} -o credentials=/tmp/smb".format(server_ip[:-1], args.volume, args.mount)
                try:
                    out = subprocess.check_output(cmd, shell=True, universal_newlines=True)
                    cmd = "rm /tmp/smb"
                    subprocess.check_output(cmd, shell=True)
                    print(TICK + "\033[32mDone!\033[0m")
                except subprocess.CalledProcessError:
                    print(CROSS+"Error while execute mount")
        else:
            print(CROSS+"This volume doesn't exist in SMB server")
    else:
        if args.volume is None and (args.mount is not None):
            print("[i]Use -m MOUNT_PINT -v DIR")
        if args.volume is not None and (args.mount is None):
            print("[i]Use -m MOUNT_PINT -v DIR")

except NotReadyError as e:
    print("[\033[31m✗\033[0m]SMB connection ERROR")