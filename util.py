import os
import platform
import psutil
import shutil
import sys

import ahocorasick_rs as ah

from media_library import Entries


def build_command(*args):
    command = [args[0]]
    if len(args) > 1:
        for i in args[1:]:
            command.append(i)
    return command


def delete_file(self):
    master_row = self.table.get_row_at(self.current_hi_row)[7]
    current_data = self.app.master[master_row]
    current_file = os.path.join(current_data.path, current_data.name)
    new_path = os.path.join(os.path.split(current_data.path)[0], "DelLinks/")
    if self.app.args.verbose:
        self.log(f"{current_file} -> {new_path}")
    if not self.app.args.no_action:
        shutil.move(current_file, new_path)
    self.set_focus(self.table)
    self.table.update_cell_at((self.current_hi_row, 0), "DELETED")


def exit_error(*error_data):
    for i, data in enumerate(error_data):
        print(data, end=" ")
        if i != len(error_data) - 1:
            print(" : ", end=" ")
    print("")
    sys.exit()


def get_path(self, index):
    path = self.app.master[index].path

    if self.app.args.translation_list and path in self.app.args.translation_list:
        path = self.app.args.translation_list[path]
    return os.path.normpath(os.path.join(path, self.app.master[index].name))


def kill_vlc(self):
    if platform.system() == "Darwin":
        try:
            cpid = psutil.Process(self.p_vlc.pid).children()[0]
        except IndexError:
            self.p_vlc = None
            return
        if cpid.name() == "VLC":
            cpid.terminate()
    else:
        self.p_vlc.terminate()
    self.p_vlc = None


def rename_file(self, new_fn):
    master_row = self.table.get_row_at(self.current_row)[7]
    current_data = self.app.master[master_row]
    current_file = os.path.join(current_data.path, current_data.name)
    new_file = os.path.join(current_data.path, new_fn)
    if self.app.args.verbose:
        self.log(f"{current_file} -> {new_file}")
    if not self.app.args.no_action:
        shutil.move(current_file, new_file)
    self.set_focus(self.table)
    self.table.update_cell_at((self.current_row, 0), new_fn)
    entry = Entries(
        path=current_data.path,
        name=new_fn,
        original_size=current_data.original_size,
        current_size=current_data.current_size,
        date=current_data.date,
        backups=current_data.backups,
        paths=current_data.paths,
        original_duration=current_data.original_duration,
        current_duration=current_data.current_duration,
        ino=current_data.ino,
        nlink=current_data.nlink,
        csum=current_data.csum,
        data=current_data.data,
    )
    self.app.master[master_row] = entry


def search_strings(master, args):
    ah_search = ah.AhoCorasick(list(map(lambda x: x.upper(), args)))
    arg_set = set(range(0, len(args)))
    file_indexes = []
    for i, item in enumerate(master):
        results = ah_search.find_matches_as_indexes(item.name.upper())
        if results != [] and set(list(zip(*results))[0]) == arg_set:
            file_indexes.append(i)
    entries = [master[i] for i in file_indexes]
    return entries
