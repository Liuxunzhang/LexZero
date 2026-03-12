"""Filter input widget"""

from textual.widgets import Input
from textual.message import Message


class FilterInput(Input):
    """Input widget for filtering table data"""

    class FilterChanged(Message):
        """Message sent when filter text changes"""

        def __init__(self, filter_text: str):
            self.filter_text = filter_text
            super().__init__()

    def __init__(self, **kwargs):
        super().__init__(placeholder="Filter results... (Ctrl+F)", **kwargs)

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes"""
        self.post_message(self.FilterChanged(event.value))
