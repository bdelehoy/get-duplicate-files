#!/usr/bin/env python3

from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
from sys import argv
import os
import hashlib
import pprint

DEFAULT_DIR = "./sample-data"
BUF_SIZE = 65536            # Update file hashes by chunks of this size in bytes (default: 65536 = 64kb)

################################################################

def get_hashes(file: Path) -> tuple:
    # Thank you Randall Hunt! https://stackoverflow.com/a/22058673
    md5 = hashlib.md5()
    sha1 = hashlib.sha1()
    sha3_256 = hashlib.sha3_256()
    with open(file, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            md5.update(data)
            sha1.update(data)
            sha3_256.update(data)
    return (md5.hexdigest(), sha1.hexdigest(), sha3_256.hexdigest())

@dataclass(order=True)
class FileEntry:
    sort_index: tuple = field(init=False, repr=False)
    file: Path
    mtime: str = field(init=False, repr=True)
    md5: str = field(init=False, repr=False)
    sha1: str = field(init=False, repr=False)
    sha3_256: str = field(init=False, repr=False)   # Used as primary key

    def __post_init__(self):
        self.mtime = datetime.fromtimestamp(self.file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S.%f')
        self.md5,self.sha1,self.sha3_256 = get_hashes(self.file)
        self.sort_index = (self.sha3_256, self.mtime, str(self.file))
    
    def get_absolute_path_as_str(self):
        return str(self.file.resolve(strict=True))
    def get_relative_path_as_str(self):
        return str(self.file)

################################################################

if __name__ == "__main__":
    dd = Path(DEFAULT_DIR)
    if len(argv) > 1:
        dd = Path(argv[1])

    #total_file_list = []            # Simple one-dimensional list of each file in dd
    num_files = 0
    hashes = defaultdict(list)      # Dictionary that maps file hashes to files that resolve to that hash
    for f in sorted(dd.rglob("*"), key=os.path.getmtime):
        # Iterate through the files by modification time (so "originals" are first)
        if f.is_file():
            new_entry = FileEntry(f)
            #total_file_list.append(new_entry)
            num_files += 1
            hashes[new_entry.sha3_256].append(new_entry)

    print("{} files, {} hashes{}".format(num_files, len(hashes), " (duplicates found)" if num_files != len(hashes) else ""))

    pp = pprint.PrettyPrinter(indent=2)
    #pp.pprint(hashes)
    #pp.pprint(total_file_list)

    print()
    all_dupes = []  # List of strings of duplicate files' absolute paths
    for h in hashes:
        if len(hashes[h]) > 1:
            dupes = hashes[h][1:]   # List of FileEntries for a single hash
            print("{} has {} duplicate(s) (SHA3-256 {})".format(hashes[h][0].get_relative_path_as_str(), len(dupes), h))
            all_dupes.extend(['"'+d.get_absolute_path_as_str()+'"' for d in dupes])
            pp.pprint(dupes)
        else:
            pass
            # print("{} has no duplicates".format(hashes[h][0].get_relative_path_as_str()))

    if len(all_dupes) > 0:
        print()
        print("Found {} duplicate file(s)".format(len(all_dupes)))
        print()
        print("Linux command to delete:")
        rm_string = "rm -f " + " ".join(all_dupes)
        print(rm_string)
        print()
        print("PowerShell command to delete:")
        powershell_string = "Remove-Item " + ", ".join(all_dupes)
        print(powershell_string)
