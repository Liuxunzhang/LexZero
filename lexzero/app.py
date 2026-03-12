"""Main TUI application"""

import logging
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import Header, Footer, Static, Input
from textual.binding import Binding
from textual.reactive import reactive

from lexzero.ui.sidebar import Sidebar
from lexzero.ui.command_input import CommandInput
from lexzero.ui.filterable_table import FilterableDataTable
from lexzero.ui.filter_input import FilterInput
from lexzero.ui.status_bar import StatusBar
from lexzero.core.volatility_wrapper_v2 import VolatilityWrapper
from lexzero.utils.exporter import ResultExporter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='/tmp/lexzero.log'
)


class LexZeroApp(App):
    """Main TUI application for Volatility3"""

    CSS = """
    Screen {
        layout: vertical;
    }

    #main-container {
        layout: horizontal;
        height: 100%;
    }

    #sidebar {
        width: 30;
        border-right: solid $primary;
        height: 100%;
    }

    #content-area {
        width: 1fr;
        layout: vertical;
    }

    #command-input {
        height: 3;
        border-bottom: solid $accent;
    }

    #filter-input {
        height: 3;
        border-bottom: solid $accent;
    }

    #main-content {
        height: 1fr;
    }

    #status-bar {
        height: 1;
        background: $boost;
        color: $text;
        padding: 0 1;
    }

    FilterableDataTable {
        height: 100%;
    }

    Tree {
        width: 100%;
        height: 100%;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+f", "focus_filter", "Filter"),
        Binding("ctrl+l", "focus_command", "Command"),
        Binding("ctrl+s", "focus_sidebar", "Sidebar"),
        Binding("ctrl+e", "export_results", "Export"),
        Binding("ctrl+r", "refresh", "Refresh"),
        Binding("tab", "focus_table", "Table", show=False),
        Binding("s", "sort_column", "Sort", show=False),
        Binding("left", "move_column_left", "Move Left", show=False),
        Binding("right", "move_column_right", "Move Right", show=False),
    ]

    current_plugin = reactive("")
    image_loaded = reactive(False)

    def __init__(self, image_path: str = None):
        super().__init__()
        self.vol_wrapper = VolatilityWrapper()
        self.image_path = image_path
        self.image_loaded = False

        # 如果提供了镜像路径，在启动后加载
        if image_path:
            self._pending_image_load = image_path
        else:
            self._pending_image_load = None

    def compose(self) -> ComposeResult:
        """Create child widgets"""
        yield Header(show_clock=True)

        # Get plugin categories
        categories = self.vol_wrapper.get_plugin_categories()

        # Get all plugin names for autocomplete
        all_plugins = []
        for plugins in categories.values():
            all_plugins.extend(plugins)

        with Container(id="main-container"):
            # Sidebar
            yield Sidebar(categories, id="sidebar")

            # Content area
            with Container(id="content-area"):
                # Command input at top
                yield CommandInput(all_plugins, id="command-input")

                # Filter input
                yield FilterInput(id="filter-input")

                # Main content area with table
                with Container(id="main-content"):
                    yield FilterableDataTable(id="results-table")

                # Status bar at bottom
                yield StatusBar(id="status-bar")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the app after mounting"""
        status_bar = self.query_one("#status-bar", StatusBar)

        # 如果有待加载的镜像，在后台加载
        if self._pending_image_load:
            self.notify(f"Loading image: {self._pending_image_load}...")
            self.run_worker(
                self._load_image_worker(self._pending_image_load),
                name="load_image",
                description="Loading memory image"
            )
        else:
            self.notify("No image loaded. Use 'load <path>' command", severity="warning")

    async def _load_image_worker(self, path: str):
        """Worker to load image in background"""
        import asyncio
        loop = asyncio.get_event_loop()

        try:
            success = await loop.run_in_executor(
                None,
                self.vol_wrapper.load_image,
                path
            )

            if success:
                self.image_path = path
                self.image_loaded = True
                status_bar = self.query_one("#status-bar", StatusBar)
                status_bar.image_name = path.split("/")[-1]
                self.notify(f"✓ Image loaded: {path}")
            else:
                self.notify(f"✗ Failed to load image: {path}", severity="error")
        except Exception as e:
            self.notify(f"✗ Error loading image: {str(e)[:50]}", severity="error")
            logging.error(f"Image load failed: {e}", exc_info=True)

    def on_filter_input_filter_changed(self, message: FilterInput.FilterChanged) -> None:
        """Handle filter changes"""
        table = self.query_one("#results-table", FilterableDataTable)
        table.filter_text = message.filter_text

        status_bar = self.query_one("#status-bar", StatusBar)
        status_bar.current_filter = message.filter_text
        status_bar.row_count = len(table._filtered_data)

    def on_sidebar_category_selected(self, message: Sidebar.CategorySelected) -> None:
        """Handle sidebar selection"""
        if message.plugin:
            self.current_plugin = message.plugin
            self.notify(f"Selected plugin: {message.plugin}")
            self.run_plugin(message.plugin)
        else:
            self.notify(f"Category: {message.category}")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle command input submission"""
        command = event.value.strip()
        if not command:
            return

        # Clear input
        event.input.value = ""

        # Parse and execute command
        self.execute_command(command)

    def execute_command(self, command: str) -> None:
        """Execute a command"""
        parts = command.split()
        if not parts:
            return

        cmd = parts[0].lower()

        if cmd == "load":
            if len(parts) < 2:
                self.notify("Usage: load <image_path>", severity="error")
                return
            self.load_image(parts[1])
        elif cmd == "help":
            self.show_help()
        elif cmd == "clear":
            self.clear_results()
        elif cmd == "clearcache":
            self.vol_wrapper.clear_cache()
            self.notify("Cache cleared")
        elif cmd == "export":
            format_type = parts[1] if len(parts) > 1 else "csv"
            self.export_with_format(format_type)
        else:
            # Assume it's a plugin name
            self.run_plugin(command)

    def load_image(self, path: str) -> None:
        """Load a memory image"""
        self.notify(f"Loading image: {path}...")
        self.run_worker(
            self._load_image_worker(path),
            name="load_image",
            description="Loading memory image"
        )

    def run_plugin(self, plugin_name: str) -> None:
        """Run a Volatility3 plugin"""
        if not self.image_loaded:
            self.notify("No image loaded", severity="error")
            return

        self.notify(f"Running plugin: {plugin_name}... (this may take a while)")
        table = self.query_one("#results-table", FilterableDataTable)
        status_bar = self.query_one("#status-bar", StatusBar)

        # Run in worker to avoid blocking UI
        self.run_worker(
            self._run_plugin_worker(plugin_name),
            name=f"plugin_{plugin_name}",
            description=f"Running {plugin_name}"
        )

    async def _run_plugin_worker(self, plugin_name: str):
        """Worker to run plugin in background"""
        table = self.query_one("#results-table", FilterableDataTable)
        status_bar = self.query_one("#status-bar", StatusBar)

        # 显示加载状态
        status_bar.is_loading = True
        status_bar.progress_text = ""

        # Progress callback to update UI
        def progress_update(message: str):
            if message.strip():
                # Update status bar with progress
                status_bar.progress_text = message
                # Only show notification for starting and completion, not progress percentages
                if "Starting:" in message or "cached" in message.lower():
                    self.notify(f"{message}")

        try:
            # Run plugin in thread pool to avoid blocking
            import asyncio
            loop = asyncio.get_event_loop()
            columns, rows = await loop.run_in_executor(
                None,
                self.vol_wrapper.run_plugin,
                plugin_name,
                progress_update
            )

            if not rows:
                self.notify(f"Plugin '{plugin_name}' returned no results", severity="warning")
                table.set_data(columns, [])
            else:
                table.set_data(columns, rows)
                self.notify(f"✓ Plugin '{plugin_name}' completed: {len(rows)} rows")

            status_bar.current_plugin = plugin_name
            status_bar.row_count = len(rows)

        except ValueError as e:
            # Plugin requirements not met
            error_msg = str(e).split('\n')[0]  # Only first line
            self.notify(f"✗ Plugin error: {error_msg}", severity="error")
            logging.error(f"Plugin execution failed: {e}")
        except Exception as e:
            self.notify(f"✗ Error: {str(e)[:80]}", severity="error")
            logging.error(f"Plugin execution failed: {e}", exc_info=True)
        finally:
            # 隐藏加载状态
            status_bar.is_loading = False
            status_bar.progress_text = ""

    def clear_results(self) -> None:
        """Clear the results table"""
        table = self.query_one("#results-table", FilterableDataTable)
        table.set_data([], [])
        status_bar = self.query_one("#status-bar", StatusBar)
        status_bar.current_plugin = ""
        status_bar.row_count = 0
        self.notify("Results cleared")

    def show_help(self) -> None:
        """Show help information"""
        help_text = """
        Commands:
        - load <path>: Load a memory image
        - clear: Clear results
        - clearcache: Clear all cached results
        - export [csv|json|txt]: Export results (default: csv)
        - help: Show this help
        - <plugin_name>: Run a plugin

        Keyboard Shortcuts:
        - Ctrl+L: Focus command line
        - Ctrl+F: Focus filter
        - Ctrl+S: Focus sidebar
        - Ctrl+E: Export results
        - Ctrl+R: Refresh current plugin (clears cache)
        - Tab: Focus table
        - Space: Select/deselect column (when in table)
        - S: Sort by selected column
        - Left/Right: Move selected column or navigate
        - Q: Quit

        Column Operations:
        1. Press Tab to focus table
        2. Use arrow keys to navigate to column
        3. Press Space to select column
        4. Use Left/Right to move selected column
        5. Press S to sort by selected column
        6. Press Space again to deselect
        """
        self.notify(help_text)

    def export_with_format(self, format_type: str) -> None:
        """Export results with specified format"""
        table = self.query_one("#results-table", FilterableDataTable)
        if not table._filtered_data:
            self.notify("No data to export", severity="warning")
            return

        if not self.current_plugin:
            self.notify("No plugin data to export", severity="warning")
            return

        # Get columns
        columns = [col.label.plain for col in table.columns.values()]

        # Export with specified format
        filepath = ResultExporter.auto_export(
            columns,
            table._filtered_data,
            self.current_plugin,
            format=format_type
        )

        if filepath:
            self.notify(f"Exported to: {filepath}")
        else:
            self.notify(f"Export failed for format: {format_type}", severity="error")

    def action_focus_command(self) -> None:
        """Focus the command input"""
        self.query_one("#command-input").focus()

    def action_focus_filter(self) -> None:
        """Focus the filter input"""
        self.query_one("#filter-input").focus()

    def action_focus_sidebar(self) -> None:
        """Focus the sidebar"""
        self.query_one("#sidebar-tree").focus()

    def action_export_results(self) -> None:
        """Export results to file"""
        table = self.query_one("#results-table", FilterableDataTable)
        if not table._filtered_data:
            self.notify("No data to export", severity="warning")
            return

        if not self.current_plugin:
            self.notify("No plugin data to export", severity="warning")
            return

        # Get columns
        columns = [col.label.plain for col in table.columns.values()]

        # Export as CSV by default
        filepath = ResultExporter.auto_export(
            columns,
            table._filtered_data,
            self.current_plugin,
            format="csv"
        )

        if filepath:
            self.notify(f"Exported to: {filepath}")
        else:
            self.notify("Export failed", severity="error")

    def action_refresh(self) -> None:
        """Refresh current plugin results"""
        if self.current_plugin:
            # Clear cache for this plugin to force refresh
            self.vol_wrapper.clear_cache(self.current_plugin)
            self.run_plugin(self.current_plugin)
        else:
            self.notify("No plugin to refresh", severity="warning")

    def action_focus_table(self) -> None:
        """Focus the column header for column operations"""
        table = self.query_one("#results-table", FilterableDataTable)
        table.focus_header()
        self.notify("Column header focused - use arrows to select, Space to confirm")

    def on_column_header_column_selected(self, message) -> None:
        """Handle column selection/deselection from header"""
        if message.is_selected:
            self.notify(f"Column '{message.name}' selected - use arrows to move, S to sort")
        else:
            self.notify(f"Column '{message.name}' deselected")

    def action_sort_column(self) -> None:
        """Sort by selected column"""
        table = self.query_one("#results-table", FilterableDataTable)
        if not table._filtered_data:
            self.notify("No data to sort", severity="warning")
            return

        if table.sort_by_selected_column():
            col_name = table.get_selected_column_name()
            direction = "↓" if table.sort_reverse else "↑"
            self.notify(f"Sorted by {col_name} {direction}")
        else:
            self.notify("No column selected", severity="warning")

    def action_move_column_left(self) -> None:
        """Move selected column to the left"""
        table = self.query_one("#results-table", FilterableDataTable)

        if table.move_selected_column_left():
            col_name = table.get_selected_column_name()
            self.notify(f"Moved '{col_name}' left")
        else:
            self.notify("Cannot move left", severity="warning")

    def action_move_column_right(self) -> None:
        """Move selected column to the right"""
        table = self.query_one("#results-table", FilterableDataTable)

        if table.move_selected_column_right():
            col_name = table.get_selected_column_name()
            self.notify(f"Moved '{col_name}' right")
        else:
            self.notify("Cannot move right", severity="warning")


def main():
    """Entry point for the application"""
    import sys

    image_path = sys.argv[1] if len(sys.argv) > 1 else None
    app = LexZeroApp(image_path)
    app.run()


if __name__ == "__main__":
    main()
