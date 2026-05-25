#!/usr/bin/env bash
# Setup script for flt — Flutter TUI Renderer
# Installs all required dependencies and launches the sample app.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

step() { echo; echo "==> $*"; echo; }

# ── 1. System dependencies ────────────────────────────────────────────────────
step "Installing system dependencies"

if command -v apt-get &>/dev/null; then
    sudo apt-get update -qq
    sudo apt-get install -y --no-install-recommends \
        curl git unzip xz-utils \
        clang libclang-dev cmake ninja-build \
        pkg-config libgtk-3-dev
elif command -v brew &>/dev/null; then
    # macOS — Homebrew provides llvm/clang; cmake and ninja for Flutter
    brew install llvm cmake ninja
    # Make llvm clang visible to bindgen
    export LIBCLANG_PATH="$(brew --prefix llvm)/lib"
else
    echo "ERROR: No supported package manager found (apt-get or brew)."
    echo "Please manually install: curl git unzip clang libclang cmake ninja"
    exit 1
fi

# ── 2. Rust ───────────────────────────────────────────────────────────────────
step "Checking Rust toolchain"

if ! command -v cargo &>/dev/null; then
    echo "Rust not found — installing via rustup..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \
        | sh -s -- -y --no-modify-path
fi

# Load cargo into PATH for this session
# shellcheck source=/dev/null
source "${CARGO_HOME:-$HOME/.cargo}/env"
echo "Rust $(rustc --version)"
echo "Cargo $(cargo --version)"

# ── 3. Flutter SDK (git submodule) ────────────────────────────────────────────
step "Initializing Flutter SDK submodule (may take a while on first run)"

# Only init the flutter submodule — skip the heavy gallery/wonderous demo apps
git -C "$SCRIPT_DIR" submodule update --init third_party/flutter

FLUTTER="$SCRIPT_DIR/third_party/flutter/bin/flutter"

# Trigger Flutter's self-setup (downloads Dart SDK, engine artifacts, etc.)
echo "Running flutter precache for linux desktop..."
"$FLUTTER" precache --linux 2>/dev/null || true

# Quick sanity check
"$FLUTTER" --version

# ── 4. Build and run ──────────────────────────────────────────────────────────
step "Building and launching the sample app"
echo "First build will download the Flutter engine (~50 MB) and compile Rust — this may take several minutes."
echo ""

# cargo run builds flt-cli, which in turn:
#   1. Runs 'flutter build bundle' on sample_app/
#   2. Downloads + links the prebuilt Flutter engine (build.rs)
#   3. Compiles the Rust TUI embedder
#   4. Launches the app in the current terminal
cargo run
