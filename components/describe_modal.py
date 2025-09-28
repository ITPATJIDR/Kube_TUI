from textual.widget import Widget
from textual.app import ComposeResult
from textual.widgets import Static, Pretty
from textual.containers import Container, Vertical, ScrollableContainer
from textual.screen import ModalScreen
from kube_api import KubeAPI


class DescribeModal(ModalScreen):
    """Modal screen for displaying kubectl describe output"""
    
    BINDINGS = [
        ("escape", "close", "Close"),
        ("q", "close", "Close"),
    ]
    
    def __init__(self, resource_type: str, resource_name: str, describe_data):
        super().__init__()
        self.resource_type = resource_type
        self.resource_name = resource_name
        self.describe_data = describe_data
    
    def compose(self) -> ComposeResult:
        with Container(classes="modal-container"):
            yield Static(f"kubectl describe {self.resource_type} {self.resource_name}", 
                        classes="modal-title")
            with ScrollableContainer(classes="modal-content"):
                yield Pretty(self.describe_data, classes="describe-output")
    
    def action_close(self) -> None:
        """Close the modal"""
        self.dismiss()
