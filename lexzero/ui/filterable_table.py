"""Data table widget with filtering, sorting and selectable headers"""

from textual.containers import Vertical
from textual.widgets import DataTable, Static
from textual.reactive import reactive
from textual.message import Message
from typing import List, Optional


class ColumnHeader(DataTable):
    """Column header as a DataTable with one row for selection"""

    selected_index = reactive(-1)
    is_column_selected = reactive(False)

    class ColumnSelected(Message):
        """Message sent when a column is selected/deselected"""
        def __init__(self, index: int, name: str, is_selected: bool):
            self.index = index
            self.name = name
            self.is_selected = is_selected
            super().__init__()

    def __init__(self, **kwargs):
        super().__init__(show_header=True, show_cursor=False, **kwargs)
        self.columns_list = []
        self.can_focus = True
        self.cursor_type = "row"

    def update_columns(self, columns: List[str]):
        """Update the column list"""
        self.columns_list = columns
        self.clear(columns=True)

        # Add columns
        for col in columns:
            self.add_column(col)

        # Add a single row with styled content
        self._refresh_row()

    def _refresh_row(self):
        """Refresh the header row with current selection state"""
        if not self.columns_list:
            return

        self.clear()

        # Create row data with styling
        row_data = []
        for i, col in enumerate(self.columns_list):
            if i == self.selected_index:
                if self.is_column_selected:
                    # Selected - use special marker
                    row_data.append(f"[bold cyan]▶ {col}[/]")
                else:
                    # Just navigating
                    row_data.append(f"[bold yellow]→ {col}[/]")
            else:
                row_data.append(col)

        self.add_row(*row_data)

    def watch_selected_index(self, new_value: int):
        """React to selection changes"""
        self._refresh_row()

    def watch_is_column_selected(self, new_value: bool):
        """React to selection state changes"""
        self._refresh_row()

    def on_key(self, event) -> None:
        """Handle key presses"""
        if event.key == "left":
            if self.is_column_selected:
                # If column is selected, let the event propagate to move column
                pass
            else:
                # Just navigating
                if self.selected_index > 0:
                    self.selected_index -= 1
                event.stop()
        elif event.key == "right":
            if self.is_column_selected:
                # If column is selected, let the event propagate to move column
                pass
            else:
                # Just navigating
                if self.selected_index < len(self.columns_list) - 1:
                    self.selected_index += 1
                event.stop()
        elif event.key == "space":
            if 0 <= self.selected_index < len(self.columns_list):
                self.is_column_selected = not self.is_column_selected
                col_name = self.columns_list[self.selected_index]
                self.post_message(self.ColumnSelected(self.selected_index, col_name, self.is_column_selected))
            event.stop()

    def on_focus(self) -> None:
        """When focused, select first column if none selected"""
        if self.selected_index == -1 and self.columns_list:
            self.selected_index = 0
            self.is_column_selected = False

    def on_blur(self) -> None:
        """When focus lost, keep selection"""
        pass


class FilterableDataTable(Vertical):
    """DataTable with selectable headers, filtering and sorting"""

    filter_text = reactive("")
    sort_column = reactive("")
    sort_reverse = reactive(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._raw_data: List[tuple] = []
        self._filtered_data: List[tuple] = []
        self._column_order: List[str] = []
        self._selected_column_index = -1
        self._header = None
        self._table = None

    def compose(self):
        """Create child widgets"""
        self._header = ColumnHeader(id="column-header")
        self._table = DataTable(id="data-table", show_header=False)
        self._table.cursor_type = "row"
        yield self._header
        yield self._table

    def set_data(self, columns: List[str], rows: List[tuple]) -> None:
        """Set table data and apply filters"""
        self._column_order = columns.copy()
        self._raw_data = rows
        self._selected_column_index = -1

        # Update header
        if self._header:
            self._header.update_columns(columns)

        # Update table
        if self._table:
            self._table.clear(columns=True)
            self._table.add_columns(*columns)

        self._apply_filter()

    def _apply_filter(self) -> None:
        """Apply current filter to data"""
        if not self.filter_text:
            self._filtered_data = self._raw_data.copy()
        else:
            filter_lower = self.filter_text.lower()
            self._filtered_data = [
                row for row in self._raw_data
                if any(filter_lower in str(cell).lower() for cell in row)
            ]

        self._apply_sort()

    def _apply_sort(self) -> None:
        """Apply current sort to filtered data"""
        if self.sort_column and self._column_order:
            try:
                col_index = self._column_order.index(self.sort_column)
                self._filtered_data.sort(
                    key=lambda x: str(x[col_index]) if col_index < len(x) else "",
                    reverse=self.sort_reverse
                )
            except (ValueError, IndexError):
                pass

        self._refresh_display()

    def _refresh_display(self) -> None:
        """Refresh the table display with filtered/sorted data"""
        if not self._table:
            return

        self._table.clear()
        for row in self._filtered_data:
            self._table.add_row(*row)

    def watch_filter_text(self, new_value: str) -> None:
        """React to filter text changes"""
        self._apply_filter()

    def watch_sort_column(self, new_value: str) -> None:
        """React to sort column changes"""
        self._apply_sort()

    def watch_sort_reverse(self, new_value: bool) -> None:
        """React to sort direction changes"""
        self._apply_sort()

    def on_column_header_column_selected(self, message: ColumnHeader.ColumnSelected):
        """Handle column selection from header"""
        if message.is_selected:
            self._selected_column_index = message.index
        else:
            self._selected_column_index = -1

    def toggle_sort(self, column: str) -> None:
        """Toggle sort for a column"""
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False

    def sort_by_selected_column(self) -> bool:
        """Sort by selected column. Returns True if sorted."""
        if 0 <= self._selected_column_index < len(self._column_order):
            col_name = self._column_order[self._selected_column_index]
            self.toggle_sort(col_name)
            return True
        return False

    def move_selected_column_left(self) -> bool:
        """Move selected column to the left. Returns True if moved."""
        if self._selected_column_index > 0:
            self.move_column(self._selected_column_index, self._selected_column_index - 1)
            self._selected_column_index -= 1
            if self._header:
                self._header.selected_index = self._selected_column_index
            return True
        return False

    def move_selected_column_right(self) -> bool:
        """Move selected column to the right. Returns True if moved."""
        if 0 <= self._selected_column_index < len(self._column_order) - 1:
            self.move_column(self._selected_column_index, self._selected_column_index + 1)
            self._selected_column_index += 1
            if self._header:
                self._header.selected_index = self._selected_column_index
            return True
        return False

    def get_selected_column_name(self) -> Optional[str]:
        """Get the name of selected column"""
        if 0 <= self._selected_column_index < len(self._column_order):
            return self._column_order[self._selected_column_index]
        return None

    def move_column(self, from_index: int, to_index: int) -> None:
        """Move a column from one position to another"""
        if not (0 <= from_index < len(self._column_order) and 0 <= to_index < len(self._column_order)):
            return

        # Store original column order before moving
        original_order = self._column_order.copy()

        # Update column order
        col_name = self._column_order.pop(from_index)
        self._column_order.insert(to_index, col_name)

        # Reorder all data (raw and filtered)
        def reorder_row(row, old_order, new_order):
            new_row = []
            for col in new_order:
                try:
                    old_index = old_order.index(col)
                    new_row.append(row[old_index] if old_index < len(row) else "")
                except:
                    new_row.append("")
            return tuple(new_row)

        self._raw_data = [reorder_row(row, original_order, self._column_order) for row in self._raw_data]
        self._filtered_data = [reorder_row(row, original_order, self._column_order) for row in self._filtered_data]

        # Update header
        if self._header:
            self._header.update_columns(self._column_order)

        # Rebuild table
        if self._table:
            self._table.clear(columns=True)
            self._table.add_columns(*self._column_order)
            self._table.clear()
            for row in self._filtered_data:
                self._table.add_row(*row)

    def focus_header(self) -> None:
        """Focus the column header"""
        if self._header:
            self._header.focus()

    def focus_table(self) -> None:
        """Focus the data table"""
        if self._table:
            self._table.focus()
