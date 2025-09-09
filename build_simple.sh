#!/bin/bash
# Simple build script for Kubernetes TUI using PyInstaller

set -e

echo "🔧 Building Kubernetes TUI executable..."

# Install PyInstaller if not already installed
if ! command -v pyinstaller &> /dev/null; then
    echo "📦 Installing PyInstaller..."
    pip install pyinstaller
fi

# Create a simple PyInstaller command
echo "🔨 Building executable..."
pyinstaller \
    --onefile \
    --name kube-tui \
    --add-data "requirements.txt:." \
    --hidden-import kubernetes \
    --hidden-import kubernetes.client \
    --hidden-import kubernetes.config \
    --hidden-import textual \
    --hidden-import textual.app \
    --hidden-import textual.containers \
    --hidden-import textual.widgets \
    --hidden-import textual.binding \
    --hidden-import rich \
    --console \
    kube_tui.py

echo "✅ Executable built successfully: dist/kube-tui"
echo "📋 To run: ./dist/kube-tui"
echo "📋 To make executable: chmod +x dist/kube-tui"

# Test the executable
echo "🧪 Testing executable..."
if [ -f "dist/kube-tui" ]; then
    chmod +x dist/kube-tui
    echo "✅ Executable is ready!"
    echo "📋 Size: $(du -h dist/kube-tui | cut -f1)"
else
    echo "❌ Build failed - executable not found"
    exit 1
fi

echo "🎉 Done! Your Kubernetes TUI executable is ready in dist/"
