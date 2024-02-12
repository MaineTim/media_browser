import os
import platform
import re
import shutil
import subprocess
import sys

import ahocorasick_rs as ah
import psutil
from rich.style import Style
from rich.text import Text

# Textual imports
from textual.widgets.data_table import RowDoesNotExist

from move_files_input import MoveFilesInput
from rename_tagged_files_input import RenameTaggedFilesInput
from write_masterfile_input import WriteMasterfileInput


def action_file_info(self):
    try:
        master_row = self.table.row_num_to_master_index(self.table.cursor_row)
    except RowDoesNotExist:
        return
    self.app.current_data = self.app.master[master_row]
    self.app.push_screen("info")


def action_move_file(self):
    self.rename_file_input.remove()
    self.move_target_input = MoveFilesInput()
    self.mount(self.move_target_input, after=self.table)
    self.move_target_input.action_delete_left_all()
    self.move_target_input.insert_text_at_cursor(self.app.move_target_path)
    self.set_focus(self.move_target_input)


# Context: BrowserDatatable
def action_run_viewer(self):
    if self.p_vlc:
        kill_vlc(self)
    if self.vlc_row == self.cursor_row:
        self.vlc_row = None
        return
    self.p_vlc = subprocess.Popen(
        build_command("vlc", get_path(self, self.row_num_to_master_index(self.cursor_row))),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    self.vlc_row = self.cursor_row


def action_tag(self):
    self.table.table_rows[self.table.cursor_row_key()].tagged = not self.table.table_rows[
        self.table.cursor_row_key()
    ].tagged
    if self.table.table_rows[self.table.cursor_row_key()].tagged:
        new_cell = Text(self.app.master[self.table.table_rows[self.table.cursor_row_key()].index].name)
        new_cell.stylize(Style(bgcolor="yellow"))
        self.table.update_cell_at((self.table.cursor_row, 0), new_cell)
        self.tag_count += 1
    else:
        new_cell = Text(self.app.master[self.table.table_rows[self.table.cursor_row_key()].index].name)
        self.table.update_cell_at((self.table.cursor_row, 0), new_cell)
        self.tag_count -= 1
    if self.app.args.verbose:
        self.log(self.tag_count)
    new_row = (
        (self.table.cursor_row + 1) if self.table.cursor_row < (self.table.row_count - 1) else self.table.row_count - 1
    )
    self.table.move_cursor(row=new_row)


def action_tagged_rename(self):
    if self.tag_count > 0:
        self.rename_file_input.remove()
        self.rename_tagged_files_input = RenameTaggedFilesInput()
        self.mount(self.rename_tagged_files_input, after=self.table)
        self.rename_tagged_files_input.action_delete_left_all()
        self.rename_tagged_files_input.insert_text_at_cursor(self.app.rename_tagged_options)
        self.set_focus(self.rename_tagged_files_input)


def action_write_masterfile(self):
    self.rename_file_input.remove()
    self.write_masterfile_input = WriteMasterfileInput()
    self.mount(self.write_masterfile_input, after=self.table)
    self.write_masterfile_input.action_delete_left_all()
    self.write_masterfile_input.insert_text_at_cursor(self.app.args.master_input_path)
    self.set_focus(self.write_masterfile_input)


def build_command(*args):
    command = [args[0]]
    if len(args) > 1:
        for i in args[1:]:
            command.append(i)
    return command


def closest_row(self):
    closest = 1000
    for key, data in self.table.table_rows.items():
        diff = abs(self.search_duration - self.app.master[data.index].original_duration)
        if diff < closest:
            closest = diff
            closest_row_key = key
    return self.table.row_key_to_row_num(closest_row_key)


def delete_file(self):
    try:
        master_index = self.table.row_num_to_master_index(self.table.cursor_row)
    except RowDoesNotExist:
        return
    current_data = self.app.master[master_index]
    if "deleted" not in current_data.data.keys():
        current_file = os.path.join(current_data.path, current_data.name)
        new_path = os.path.join(os.path.split(current_data.path)[0], "DelLinks/")
        if self.app.args.verbose:
            self.log(f"{current_file} -> {new_path}")
        if not self.app.args.no_action:
            shutil.move(current_file, new_path)
        self.app.master[master_index].data["deleted"] = True
        self.app.changed.append((master_index, "D", ""))
    self.set_focus(self.table)
    self.table.remove_row(self.table.cursor_row_key())


def exit_error(*error_data):
    for i, data in enumerate(error_data):
        print(data, end=" ")
        if i != len(error_data) - 1:
            print(" : ", end=" ")
    print("")
    sys.exit()


def get_path(self, index):
    path = self.app.master[index].path
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


def move_file(self):
    if self.app.args.verbose:
        self.log(f"{self.current_file} -> {self.new_file}")
    if not self.app.args.no_action:
        shutil.move(self.current_file, self.new_file)
        os.utime(self.new_file, (self.current_file_utime, self.current_file_utime))


def parse_target_strings(args):
    """
    Create a regex that will match the set of targets given.
    "OR" is the only boolean implemented.
    """
    target_regex = ""
    targets = []
    or_count = 0
    i = -1
    for token in args:
        while (quote := token.find('"')) != -1:
            if (quote > 0) and token[quote - 1] == chr(92):
                token = remove_char(token, quote - 1)
            else:
                token = remove_char(token, quote)
        i += 1
        if token == "OR" and i > 0 and len(args) > i:
            if or_count < 1:
                target_regex = target_regex[: len(target_regex) - 1] + "[" + target_regex[len(target_regex) - 1 :]
            or_count = 2
            i -= 1
        else:
            if or_count == 1:
                target_regex += "]"
            target_regex += str(i)
            targets.append(token)
            or_count -= 1
    if or_count > 0:
        target_regex += "]"
    return target_regex, targets


def remove_char(string, index):
    if index == 0:
        return string[1:]
    elif index == len(string) - 1:
        return string[:-1]
    else:
        return string[:index] + string[index + 1 :]


def rename_file(self):
    if self.app.args.verbose:
        self.log(f"{self.current_file} -> {self.new_file}")
    if not self.app.args.no_action:
        shutil.move(self.current_file, self.new_file)
    self.parent.set_focus(self.parent.table)
    self.parent.table.update_cell_at((self.parent.table.cursor_row, 0), os.path.basename(self.new_file))
    self.app.master[self.master_row].name = os.path.basename(self.new_file)
    self.app.changed.append((self.master_row, "R", os.path.basename(self.new_file)))


def search_duration(self, master, args):
    duration_target = args[0][1:].split(".")
    duration_seconds = 0.0
    try:
        for i, m in enumerate(reversed(duration_target)):
            duration_seconds += float(m) * (60.0**i)
    except (ValueError, IndexError):
        return []
    if self.app.args.verbose:
        self.log(f"Time we calculated: {duration_target} : {duration_seconds}")
    return (
        duration_seconds,
        [
            master[index]
            for index, item in enumerate(master)
            if (item.current_duration - 300.0) < duration_seconds < (item.current_duration + 300)
        ],
    )


def search_strings(self, master, args, case_insensitive=True):
    """
    Search each entry in master, finding hits against a list of targets.
    Then match that list to a regex, and return the list of indexes to entries that match.
    """
    target_regex, targets = parse_target_strings(args)
    if case_insensitive:
        ah_search = ah.AhoCorasick(list(map(lambda x: x.upper(), targets)))
    else:
        ah_search = ah.AhoCorasick(targets)
    file_indexes = []
    for i, item in enumerate(master):
        if "deleted" not in item.data.keys():
            if case_insensitive:
                results = ah_search.find_matches_as_indexes(item.name.upper())
            else:
                results = ah_search.find_matches_as_indexes(item.name)
            if results != []:
                results.sort(key=lambda x: x[0])
                tokens = "".join([str(x) for x in (list(zip(*results))[0])])
                if re.search(target_regex, tokens):
                    file_indexes.append(i)
    return [master[index] for index in file_indexes]
