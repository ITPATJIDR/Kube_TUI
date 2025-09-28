from textual.app import App, ComposeResult
from kubernetes import client, config
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, OptionList
from components.namespace import Namespace
from components.api_resource_list import ApiResourceList
from components.api_resource_content import ApiResourceContent
from textual import log
from textual.widgets import Footer, Header
import sys
import os

class KubeTui(App):
    config.load_kube_config() 
    
    # Handle CSS path for both development and PyInstaller
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Running as script
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    CSS_PATH = os.path.join(base_path, "kube.tcss")

    BINDINGS = [
        ("up", "arrow_up", "Up"),
        ("down", "arrow_down", "Down"),
        ("left", "arrow_left", "Left"),
        ("right", "arrow_right", "Right"),
        ("enter", "enter", "Enter"),
    ]

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("namespace", classes="box box_1", id="namespace_box"),
            ApiResourceList(classes="box box_2", id="api_box"),
        )
        yield Container(
            OptionList(id="namespace_list"),
            classes="box box_3",
            id="main_content",
        )
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(".box_1").can_focus = True
        self.query_one(".box_2").can_focus = True
        self.query_one("#main_content").can_focus = True

        try:
            contexts, active = config.list_kube_config_contexts()
            self.current_namespace = active.get("context", {}).get("namespace", "default")
        except Exception:
            self.current_namespace = "default"
        self.query_one("#namespace_box", Static).update(f"namespace: {self.current_namespace}")

        self.current_box = "box_1"
        self.left_last = "box_1"
        self._apply_focus("box_1")

        self.selecting_namespace = False
        self.query_one("#namespace_list", OptionList).display = False

    def _apply_focus(self, target: str) -> None:
        for name in ("box_1", "box_2", "box_3"):
            widget = self.query_one(f".{name}")
            widget.remove_class("focused")
        target_widget = self.query_one(f".{target}")
        target_widget.add_class("focused")
        target_widget.focus()
        self.current_box = target
        if target in ("box_1", "box_2"):
            self.left_last = target

    def _set_main_content(self, widget) -> None:
        main = self.query_one("#main_content", Container)
        for child in list(main.children):
            child.remove()
        main.mount(widget)

    def action_arrow_up(self) -> None:
        if self.current_box == "box_2":
            self._apply_focus("box_1")

    def action_arrow_down(self) -> None:
        if self.current_box == "box_1":
            self._apply_focus("box_2")

    def action_arrow_left(self) -> None:
        if self.current_box == "box_3":
            self._apply_focus(self.left_last)

    def action_arrow_right(self) -> None:
        if self.current_box in ("box_1", "box_2"):
            self._apply_focus("box_3")

    def action_enter(self) -> None:
        if self.current_box == "box_1":
            self._set_main_content(Namespace())
            self._apply_focus("box_3")
        elif self.current_box == "box_2":
            api_widget = self.query_one("#api_box", ApiResourceList)
            api_widget.action_focus_list()
        elif self.current_box == "box_3":
            print("Enter pressed in box 3")
            main = self.query_one("#main_content", Container)
            for child in main.children:
                if isinstance(child, Namespace):
                    child.action_select()
                    break
                elif isinstance(child, ApiResourceContent):
                    child.action_focus_table()
                    break

if __name__ == "__main__":
    app = KubeTui()
    app.run()