# Media Library Version 23-03-15-a

import bisect
import csv
import datetime
import hashlib
import operator
import os
import pickle
from dataclasses import dataclass, field

import ffmpeg

# Obsolete entry schema.
# FileEntries = typing.NamedTuple(
#     "FileEntries",
#     [
#         ("path", str),
#         ("name", str),
#         ("original_size", int),
#         ("current_size", int),
#         ("date", datetime.datetime),
#         ("backups", int),
#         ("paths", typing.List),
#         ("original_duration", float),
#         ("current_duration", float),
#         ("ino", int),
#         ("nlink", int),
#         ("csum", str),
#         ("data", typing.Dict),
#     ],
# )


@dataclass
class Entries:
    UID: str = ""
    path: str = ""
    name: str = ""
    original_size: int = 0
    current_size: int = 0
    date: datetime.datetime = datetime.datetime.now()
    backups: int = 0
    paths: list = field(default_factory=list)
    original_duration: float = 0.0
    current_duration: float = 0.0
    ino: int = 0
    nlink: int = 0
    csum: str = ""
    data: dict = field(default_factory=dict)


def checksum(filename, hash_factory=hashlib.md5, chunk_num_blocks=128):
    h = hash_factory()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_num_blocks * h.block_size), b""):
            h.update(chunk)
    return h.hexdigest()


def file_duration(filename):
    duration = 0
    try:
        info = ffmpeg.probe(filename)
        duration = info["format"]["duration"]
    except ffmpeg.Error as e:
        print()
        print(e.stderr)
        print()
        return -1
    return duration


def check_inode(database, inode, start=0):
    for i, item in enumerate(database):
        if item.ino == inode:
            return (True, i)
    return (False, 0)


# Return True, result if size matches.
def check_size(database, size, start=0):
    entry_size = operator.attrgetter("current_size")

    if start > 0:
        result = start + 1
    else:
        result = bisect.bisect_left(database, size, key=entry_size)
    if result >= len(database) or database[result].current_size != size:
        return (False, 0)
    else:
        return (True, result)


# Return True, result if size and name match.
def check_db(database, item):
    start = 0
    while True:
        found, result = check_size(database, item.current_size, start)
        if found:
            if database[result].name == item.name:
                return True, result
            else:
                start = result
        else:
            return False, 0


def split_backup_path(path):
    split_point = path.find("[")
    end_point = path.find("]")
    return os.path.normpath(path[0:split_point]), int(path[split_point + 1 : end_point])


def create_file_entry(path, update_duration = False):
    stat_entry = os.stat(path)
    if update_duration:
        duration = file_duration(path)
    else:
        duration = 0.0
    entry = Entries(
        path=os.path.dirname(path),
        name=os.path.basename(path),
        original_size=stat_entry.st_size,
        current_size=stat_entry.st_size,
        date=datetime.datetime.fromtimestamp(stat_entry.st_mtime, tz=datetime.timezone.utc),
        backups=0,
        paths=[],
        original_duration=duration,
        current_duration=duration,
        ino=stat_entry.st_ino,
        nlink=stat_entry.st_nlink,
        csum="",
        data={},
    )
    return entry


def create_file_list(path, update_duration = False):
    entry_size = operator.attrgetter("current_size")
    file_entries = []
    files = [
        f
        for f in os.listdir(path)
        if os.path.isfile(os.path.join(path, f)) and os.path.splitext(f)[1] in [".mp4", ".mp4~"]
    ]
    for f in files:
        entry = create_file_entry(os.path.join(path, f), update_duration)
        bisect.insort(file_entries, entry, key=entry_size)
    return file_entries


def read_master_file(master_input_path):
    if os.path.exists(master_input_path):
        with open(master_input_path, "rb") as f:
            master = pickle.load(f)
        print(f"{len(master)} records found.")
        return master
    else:
        return []


def write_entries_file(master: list, master_output_path: str, write_csv: bool):
    with open(master_output_path, "wb") as f:
        pickle.dump(master, f)

    if write_csv:
        csv_output_path = master_output_path + ".csv"
        with open(csv_output_path, "w") as f:
            w = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
            w.writerow(
                [
                    "Serialnum",
                    "Path",
                    "Name",
                    "Ext",
                    "O_Size",
                    "C_Size",
                    "Date",
                    "Backups",
                    "Paths",
                    "O_Duration",
                    "C_Duration",
                    "Ino",
                    "Nlink",
                ]
            )
            w.writerows(
                [
                    item.UID,
                    item.path,
                    item.name,
                    item.original_size,
                    item.current_size,
                    item.date,
                    item.backups,
                    item.paths,
                    item.original_duration,
                    item.current_duration,
                    item.ino,
                    item.nlink,
                    item.csum,
                    item.data,
                ]
                for item in master
            )
    print(f"{len(master)} records written.")
