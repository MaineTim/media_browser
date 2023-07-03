import time
from dataclasses import dataclass

from rich.text import Text
from textual.widgets import DataTable


@dataclass
class BrowserRow:
    index: int
    tagged: bool = False


class BrowserDataTable(DataTable):
    def __init__(self, columns, entries, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.column_keys = []
        self.enter_pressed = False
        self.table_rows = self.build_table(columns, entries)

    def add_row(self, *args, **kwargs):
        return super().add_row(Text(args[0]), *args[1:], **kwargs)

    def build_table(self, columns, entries):
        if self.app.args.verbose:
            self.log(f"{len(entries)} records found.")
        self.cursor_type = "row"
        for c in columns:
            self.column_keys.append(self.add_column(c[0], width=c[1]))
        return self.populate_rows(entries)

    def cursor_row_key(self):
        row_key, _ = self.coordinate_to_cell_key(self.cursor_coordinate)
        return row_key

    def index_to_row_key(self, index):
        for key, values in self.table_rows.items():
            if values.index == index:
                return key
        return None

    def on_key(self, event):
        if event.key == "enter":
            self.enter_pressed = True

    def populate_rows(self, entries):
        table_rows = {}
        for item in entries:
            if "deleted" not in item.data.keys():
                minute, sec = divmod(float(item.original_duration), 60)
                table_rows[
                    self.add_row(
                        item.name,
                        item.original_size,
                        item.current_size,
                        item.date.strftime("%Y-%m-%d %H:%M:%S"),
                        item.backups,
                        time.strftime("%H:%M:%S", time.gmtime(float(item.original_duration))),
                        f"{round(minute):03}:{round(sec):02}",
                        time.strftime("%H:%M:%S", time.gmtime(float(item.current_duration))),
                    )
                ] = BrowserRow(item.data["index"], tagged=False)
        return table_rows

    def row_key_to_master_attr(self, row_key, attrstr):
        attr = getattr(self.app.master[self.table_rows[row_key].index], attrstr)
        return attr

    def row_key_to_row_num(self, row_key):
        for i, item in enumerate(self.ordered_rows):
            if item.key == row_key:
                return i
        return -1

    def row_num_to_master_attr(self, row_num, attrstr):
        row_key = self.row_num_to_row_key(row_num)
        attr = getattr(self.app.master[self.table_rows[row_key].index], attrstr)
        return attr

    def row_num_to_master_index(self, row_num):
        row_key = self.row_num_to_row_key(row_num)
        return self.table_rows[row_key].index

    def row_num_to_row_key(self, row: int):
        row_key, _ = self.coordinate_to_cell_key((row, 0))
        return row_key
