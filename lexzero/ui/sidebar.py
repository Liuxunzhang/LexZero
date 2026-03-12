"""Sidebar menu widget for navigation"""

from textual.app import ComposeResult
from textual.widgets import Tree
from textual.containers import Container
from textual.message import Message


class Sidebar(Container):
    """Sidebar navigation menu"""

    class CategorySelected(Message):
        """Message sent when a category is selected"""

        def __init__(self, category: str, plugin: str = None):
            self.category = category
            self.plugin = plugin
            super().__init__()

    def __init__(self, categories: dict, **kwargs):
        super().__init__(**kwargs)
        self.categories = categories

    def compose(self) -> ComposeResult:
        """Create child widgets"""
        tree = Tree("", id="sidebar-tree")
        tree.root.expand()
        tree.show_root = False  # Hide the root node

        for category, plugins in self.categories.items():
            category_node = tree.root.add(category, expand=False)
            for plugin in plugins:
                category_node.add_leaf(plugin)

        yield tree

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle tree node selection"""
        node = event.node
        if node.parent and node.parent != self.query_one("#sidebar-tree").root:
            # Plugin selected
            category = node.parent.label
            plugin = str(node.label)
            self.post_message(self.CategorySelected(category, plugin))
        elif node != self.query_one("#sidebar-tree").root:
            # Category selected
            category = str(node.label)
            self.post_message(self.CategorySelected(category))
