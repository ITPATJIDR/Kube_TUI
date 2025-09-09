# Building Kubernetes TUI

This document explains how to build the Kubernetes TUI as a standalone executable or AppImage.

## Prerequisites

- Python 3.8+
- pip
- Linux system (for AppImage)

## Option 1: Simple Executable (Recommended)

The easiest way to build a standalone executable:

```bash
# Make sure you're in the project directory
cd /home/itpat/Code/Python/kube_tui

# Run the simple build script
./build_simple.sh
```

This will create a single executable file in `dist/kube-tui` that you can run anywhere.

## Option 2: AppImage (Portable Linux App)

To build a proper AppImage that can run on any Linux system:

```bash
# Run the AppImage build script
./build_appimage.sh
```

This will create `kube-tui-x86_64.AppImage` which is a portable Linux application.

## Manual Build

If you prefer to build manually:

### 1. Install PyInstaller

```bash
pip install pyinstaller
```

### 2. Build Executable

```bash
pyinstaller --onefile --name kube-tui kube_tui.py
```

### 3. Test the Build

```bash
# Make executable
chmod +x dist/kube-tui

# Test it
./dist/kube-tui
```

## Build Options

### PyInstaller Options Used

- `--onefile`: Creates a single executable file
- `--name kube-tui`: Sets the executable name
- `--console`: Keeps the console window (needed for TUI)
- `--hidden-import`: Includes required modules that PyInstaller might miss

### AppImage Features

- **Portable**: Runs on any Linux distribution
- **Self-contained**: No need to install Python or dependencies
- **Desktop Integration**: Can be added to application menus
- **Icon Support**: Includes application icon

## Troubleshooting

### Common Issues

1. **Missing Dependencies**: Make sure all required packages are installed
2. **Import Errors**: Use `--hidden-import` for any missing modules
3. **Large File Size**: This is normal for PyInstaller builds with many dependencies

### File Sizes

- Simple executable: ~50-100MB
- AppImage: ~60-120MB

The large size is due to including the entire Python runtime and all dependencies.

## Distribution

### Simple Executable
- Copy `dist/kube-tui` to any Linux system
- Make it executable: `chmod +x kube-tui`
- Run: `./kube-tui`

### AppImage
- Copy `kube-tui-x86_64.AppImage` to any Linux system
- Make it executable: `chmod +x kube-tui-x86_64.AppImage`
- Run: `./kube-tui-x86_64.AppImage`

## Requirements

The built executable will still require:
- A valid kube config file (`~/.kube/config`)
- Access to a Kubernetes cluster
- Terminal that supports TUI (most modern terminals work)

## Notes

- The executable is built for the current architecture (x86_64)
- For other architectures, you'll need to build on that specific system
- The AppImage is more portable but larger than the simple executable
