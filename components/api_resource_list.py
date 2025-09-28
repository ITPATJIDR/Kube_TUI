from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import OptionList, Static
from kube_api import KubeAPI
from components.api_resource_content import ApiResourceContent


class ApiResourceList(Widget):
    BINDINGS = [
        ("enter", "focus_list", "Focus List"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.list_focused = False

    def compose(self) -> ComposeResult:
        yield Static("API Resources", id="api_title")
        yield OptionList(id="api_list")

    def on_mount(self) -> None:
        try:
            kube_api = KubeAPI()
            api_resources = kube_api.get_api_resources()
            
            option_list = self.query_one("#api_list", OptionList)
            option_list.clear_options()
            
            for resource in api_resources:
                name = resource['name']
                display_text = f"{name}"
                option_list.add_option(display_text)
        except Exception as e:
            option_list = self.query_one("#api_list", OptionList)
            option_list.clear_options()
            for name in ["pods", "services", "deployments", "configmaps", "secrets"]:
                option_list.add_option(name)

    def action_focus_list(self) -> None:
        """Focus the OptionList when Enter is pressed on the widget"""
        try:
            option_list = self.query_one("#api_list", OptionList)
            option_list.focus()
            self.list_focused = True
        except Exception:
            pass

    def on_key(self, event) -> None:
        """Handle key events when the list is focused"""
        if self.list_focused:
            option_list = self.query_one("#api_list", OptionList)
            if option_list.has_focus:
                if event.key == "enter":
                    try:
                        index = getattr(option_list, "highlighted", getattr(option_list, "highlighted_index", 0))
                        opt = option_list.get_option_at_index(index)
                        selected = getattr(opt, "value", getattr(opt, "prompt", str(opt)))
                        if selected.startswith("Option('") and selected.endswith("')"):
                            selected = selected[8:-2]  
                        selected = selected.split(' (')[0]  
                        if selected:
                            print("Selected API resource: ", selected)
                            setattr(self.app, "selected_api_resource", selected)
                            
                            app = self.app
                            main = app.query_one("#main_content")
                            
                            for child in list(main.children):
                                child.remove()
                            main.mount(ApiResourceContent())
                    except Exception:
                        pass
                elif event.key == "escape":
                    self.focus()
                    self.list_focused = False
                else:
                    return
            else:
                self.list_focused = False