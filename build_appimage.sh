#!/bin/bash
# Build script for Kubernetes TUI AppImage

set -e

echo "🔧 Building Kubernetes TUI AppImage..."

# Check if we're in the right directory
if [ ! -f "kube_tui.py" ]; then
    echo "❌ Error: kube_tui.py not found. Please run this script from the project directory."
    exit 1
fi

# Create build directory
BUILD_DIR="build"
mkdir -p "$BUILD_DIR"

# Install PyInstaller if not already installed
if ! command -v pyinstaller &> /dev/null; then
    echo "📦 Installing PyInstaller..."
    pip install pyinstaller
fi

# Create PyInstaller spec file
cat > kube_tui.spec << 'EOF'
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['kube_tui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'kubernetes',
        'kubernetes.client',
        'kubernetes.config',
        'textual',
        'textual.app',
        'textual.containers',
        'textual.widgets',
        'textual.binding',
        'rich',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='kube-tui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
EOF

echo "🔨 Building executable with PyInstaller..."
pyinstaller --clean kube_tui.spec

# Create AppDir structure
echo "📁 Creating AppDir structure..."
APPDIR="kube-tui.AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"

# Copy executable
cp dist/kube-tui "$APPDIR/usr/bin/"

# Create desktop file
cat > "$APPDIR/kube-tui.desktop" << 'EOF'
[Desktop Entry]
Name=Kubernetes TUI
Comment=A modern terminal user interface for Kubernetes resource management
Exec=kube-tui
Icon=kube-tui
Type=Application
Categories=System;TerminalEmulator;Development;
Terminal=true
EOF

# Create AppRun script
cat > "$APPDIR/AppRun" << 'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
exec "${HERE}/usr/bin/kube-tui" "$@"
EOF
chmod +x "$APPDIR/AppRun"

# Create a simple icon (if you have one, replace this)
echo "🎨 Creating icon..."
# You can replace this with a real icon file
cat > "$APPDIR/usr/share/icons/hicolor/256x256/apps/kube-tui.png" << 'EOF'
# This is a placeholder - replace with actual PNG icon
EOF

# Download and use AppImageTool
echo "📥 Downloading AppImageTool..."
if [ ! -f "appimagetool-x86_64.AppImage" ]; then
    wget -q https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
    chmod +x appimagetool-x86_64.AppImage
fi

# Build AppImage
echo "🚀 Building AppImage..."
./appimagetool-x86_64.AppImage "$APPDIR" "kube-tui-x86_64.AppImage"

echo "✅ AppImage built successfully: kube-tui-x86_64.AppImage"
echo "📋 To run: ./kube-tui-x86_64.AppImage"
echo "📋 To make executable: chmod +x kube-tui-x86_64.AppImage"

# Cleanup
echo "🧹 Cleaning up..."
rm -rf "$APPDIR"
rm -rf build/
rm -rf dist/
rm -rf __pycache__/
rm -f kube_tui.spec

echo "🎉 Done! Your Kubernetes TUI AppImage is ready."
