# Kubernetes TUI

A modern Terminal User Interface (TUI) for Kubernetes resource management built with Python and Textual.

## Features

- 🎨 **Modern UI**: Clean, responsive terminal interface with modern styling
- 🔧 **Kube Config Input**: Centered input screen for kube config path
- 📦 **Resource Browser**: Sidebar with Kubernetes resources and counts
- ⌨️ **Arrow Key Navigation**: Use UP/DOWN arrows to navigate resources
- 📊 **Resource Details**: View detailed information about selected resources
- 🚀 **Real-time Data**: Live resource counts and status information

## Screenshots

The application features:
1. **Initial Screen**: Centered input for kube config path
2. **Main Interface**: Sidebar with resource list and main content area
3. **Resource Details**: Detailed view of selected Kubernetes resources

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd kube_tui
   ```

2. **Create and activate virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Run the application**:
   ```bash
   python run.py
   # or
   python kube_tui.py
   ```

2. **Enter kube config path**:
   - Default: `~/.kube/config`
   - Press Enter to connect

3. **Navigate resources**:
   - Use UP/DOWN arrow keys to navigate the sidebar
   - Press Enter to select a resource
   - View detailed information in the main content area

4. **Exit**:
   - Press `q`, `Ctrl+C`, or `Escape` to quit

## Requirements

- Python 3.8+
- Kubernetes cluster access
- Valid kube config file

## Dependencies

- `textual`: Modern TUI framework
- `kubernetes`: Kubernetes Python client
- `rich`: Rich text and beautiful formatting

## Supported Resources

- **Pods**: View pod status and details
- **Services**: List services and their types
- **Deployments**: Show deployment status and replica counts
- **ReplicaSets**: View replica set information
- **ConfigMaps**: List configuration maps
- **Secrets**: View secret resources
- **Nodes**: Display node status and information
- **Namespaces**: List available namespaces
- **StatefulSets**: View stateful set resources
- **DaemonSets**: List daemon set resources

## Architecture

The application is built with a modular architecture:

- `KubeConfigInput`: Initial screen for config path input
- `ResourceSidebar`: Sidebar with resource list and navigation
- `ResourceItem`: Individual resource items with counts
- `MainContent`: Main content area for resource details
- `KubeTUI`: Main application class with event handling

## Development

To contribute or modify the application:

1. Install development dependencies
2. Make your changes
3. Test with a local Kubernetes cluster
4. Submit a pull request

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## Support

For support, please open an issue in the repository or contact the maintainers.
