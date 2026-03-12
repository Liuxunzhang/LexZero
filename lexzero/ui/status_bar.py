"""Status bar widget showing current state"""

from textual.widgets import Static
from textual.reactive import reactive


class StatusBar(Static):
    """Status bar showing current plugin, filter, and image info"""

    current_plugin = reactive("")
    current_filter = reactive("")
    image_name = reactive("")
    row_count = reactive(0)
    is_loading = reactive(False)
    progress_text = reactive("")  # Progress percentage text

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def render(self) -> str:
        """Render the status bar"""
        parts = []

        if self.is_loading:
            if self.progress_text:
                parts.append(f"⏳ {self.progress_text}")
            else:
                parts.append("⏳ Loading...")

        if self.image_name:
            parts.append(f"Image: {self.image_name}")

        if self.current_plugin:
            parts.append(f"Plugin: {self.current_plugin}")

        if self.current_filter:
            parts.append(f"Filter: {self.current_filter}")

        if self.row_count > 0:
            parts.append(f"Rows: {self.row_count}")

        return " | ".join(parts) if parts else "Ready"
