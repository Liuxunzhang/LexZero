"""Command input widget with autocomplete support"""

from textual.widgets import Input
from textual.suggester import Suggester
from typing import List, Optional


class CommandSuggester(Suggester):
    """Suggester for Volatility3 commands"""

    def __init__(self, commands: List[str]):
        super().__init__()
        self.commands = sorted(commands)

    async def get_suggestion(self, value: str) -> Optional[str]:
        """Get command suggestion based on current input"""
        if not value:
            return None

        for command in self.commands:
            if command.startswith(value.lower()):
                return command

        return None


class CommandInput(Input):
    """Command input widget with autocomplete"""

    def __init__(self, commands: List[str], **kwargs):
        suggester = CommandSuggester(commands)
        super().__init__(
            placeholder="Enter command...",
            suggester=suggester,
            **kwargs
        )
