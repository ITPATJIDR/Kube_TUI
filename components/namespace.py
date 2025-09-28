from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import OptionList
from kubernetes import client
from textual.widgets import Static  


class Namespace(Widget):
    BINDINGS = [("enter", "select", "Select Namespace")]

    def compose(self) -> ComposeResult:
        yield Static("Select Namespace", id="ns_title")
        yield OptionList(id="namespace_list")

    def on_mount(self) -> None:
        try:
            v1 = client.CoreV1Api()
            ns_items = v1.list_namespace().items
            namespaces = [ns.metadata.name for ns in ns_items]
        except Exception:
            namespaces = ["default"]
        option_list = self.query_one("#namespace_list", OptionList)
        option_list.clear_options()
        for name in namespaces:
            option_list.add_option(name)
        option_list.focus()

    def action_select(self) -> None:
        option_list = self.query_one("#namespace_list", OptionList)
        index = getattr(option_list, "highlighted", getattr(option_list, "highlighted_index", 0))
        try:
            opt = option_list.get_option_at_index(index)
            selected = getattr(opt, "value", getattr(opt, "prompt", str(opt)))
        except Exception:
            selected = None
        if selected:
            setattr(self.app, "current_namespace", selected)
            self.app.query_one("#namespace_box", Static).update(f"namespace: {selected}")
            if hasattr(self.app, "_apply_focus"):
                self.app._apply_focus("box_1")
            self.remove()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        selected = getattr(event.option, "value", None) or getattr(event.option, "prompt", None) or str(event.option)
        if selected:
            setattr(self.app, "current_namespace", selected)
            self.app.query_one("#namespace_box", Static).update(f"namespace: {selected}")
            if hasattr(self.app, "_apply_focus"):
                self.app._apply_focus("box_1")
            self.remove()
        event.stop()
