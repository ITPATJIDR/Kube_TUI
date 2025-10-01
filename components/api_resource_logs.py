from textual.widget import Widget
from textual.app import ComposeResult, RenderResult
from textual.widgets import Static
from textual.containers import Container, Vertical, ScrollableContainer
from textual.screen import ModalScreen
from kube_api import KubeAPI
from textual.timer import Timer


class ApiResourceLogs(ModalScreen):
    """Modal screen for displaying logs of a selected resource"""
    
    BINDINGS = [
        ("escape", "close", "Close"),
        ("q", "close", "Close"),
        ("ctrl+w", "toggle_watch", "Toggle Watch"),
        ("ctrl+r", "refresh", "Refresh"),
    ]
    
    def __init__(self, resource_type: str, resource_name: str, namespace: str = "default"):
        super().__init__()
        self.resource_type = resource_type
        self.resource_name = resource_name
        self.namespace = namespace
        self.watch_enabled = False
        self.watch_timer = None
        self.logs_content = ""
        
    def compose(self) -> ComposeResult:
        with Container(classes="modal-container"):
            yield Static(f"kubectl logs {self.resource_name} -n {self.namespace}", 
                        classes="modal-title", id="logs_title")
            with ScrollableContainer(classes="modal-content", id="logs_container"):
                yield Static("", id="logs_content")
    
    def on_mount(self) -> None:
        """Called when the modal is mounted"""
        self._fetch_logs()
        self._update_title()
    
    def on_unmount(self) -> None:
        """Clean up when modal is unmounted"""
        self._stop_watch()
    
    def action_close(self) -> None:
        """Close the modal"""
        self.dismiss()
    
    def action_toggle_watch(self) -> None:
        """Toggle watch mode for logs"""
        if self.watch_enabled:
            self._stop_watch()
            self.notify("Watch stopped", title="Info")
        else:
            self._start_watch()
            self.notify(f"Watching logs for {self.resource_name} (refresh every 2s)", title="Info")
        
        self._update_title()
    
    def action_refresh(self) -> None:
        """Refresh logs manually"""
        self._fetch_logs()
        self.notify("Logs refreshed", title="Info")
    
    def _start_watch(self) -> None:
        """Start the watch timer"""
        self.watch_enabled = True
        # Refresh every 2 seconds for logs
        self.watch_timer = self.set_timer(2.0, self._refresh_logs)
    
    def _stop_watch(self) -> None:
        """Stop the watch timer"""
        self.watch_enabled = False
        if self.watch_timer:
            self.watch_timer.stop()
            self.watch_timer = None
    
    def _refresh_logs(self) -> None:
        """Refresh logs when in watch mode"""
        if self.watch_enabled:
            self._fetch_logs()
            # Reschedule the timer for continuous watching
            self.watch_timer = self.set_timer(2.0, self._refresh_logs)
    
    def _update_title(self) -> None:
        """Update the title with watch status"""
        title_widget = self.query_one("#logs_title", Static)
        
        if self.watch_enabled:
            watch_indicator = "🔴 "
            watch_status = " [WATCHING]"
        else:
            watch_indicator = "⚪ "
            watch_status = ""
        
        title_widget.update(f"{watch_indicator}kubectl logs {self.resource_name} -n {self.namespace}{watch_status}")
    
    def _fetch_logs(self) -> None:
        """Fetch logs for the resource"""
        try:
            kube_api = KubeAPI()
            logs_content_widget = self.query_one("#logs_content", Static)
            
            # Check if the resource supports logs (only pods typically do)
            if self.resource_type.lower() != "pods":
                logs_content_widget.update(f"❌ Logs are only available for pods, not {self.resource_type}")
                return
            
            # Get logs using the Kubernetes API
            logs = self._get_pod_logs(kube_api)
            
            if logs:
                self.logs_content = logs
                logs_content_widget.update(logs)
            else:
                logs_content_widget.update(f"No logs available for {self.resource_name}")
                
        except Exception as e:
            logs_content_widget = self.query_one("#logs_content", Static)
            logs_content_widget.update(f"Error fetching logs: {str(e)}")
    
    def _get_pod_logs(self, kube_api: KubeAPI) -> str:
        """Get logs for a specific pod"""
        try:
            # Use the Kubernetes Python client to get logs
            logs = kube_api.v1.read_namespaced_pod_log(
                name=self.resource_name,
                namespace=self.namespace,
                follow=False,  # Don't follow, we'll refresh manually
                tail_lines=100  # Get last 100 lines
            )
            return logs
        except Exception as e:
            # If the pod doesn't exist or has no logs, try to get more specific error
            try:
                # Check if pod exists
                pod = kube_api.v1.read_namespaced_pod(
                    name=self.resource_name,
                    namespace=self.namespace
                )
                
                # If pod exists but no logs, it might be a completed job or similar
                if pod.status.phase in ["Succeeded", "Failed"]:
                    return f"Pod {self.resource_name} is in {pod.status.phase} state - no active logs available"
                else:
                    return f"No logs available for pod {self.resource_name} (status: {pod.status.phase})"
                    
            except Exception as pod_error:
                return f"Error: Pod {self.resource_name} not found in namespace {self.namespace}: {str(pod_error)}"
