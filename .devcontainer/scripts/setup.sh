#!/bin/bash
set -e

echo "Starting AWS Project setup..."

export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"


echo "Trusting mise config..."
mise trust

if command -v mise >/dev/null 2>&1; then
    eval "$(mise activate bash)"
fi

echo "Installing tools via mise..."
mise install --yes

if [ ! -d "$HOME/.config/nvim" ]; then
    echo "Cloning LazyVim..."
    git clone https://github.com/LazyVim/starter $HOME/.config/nvim
    rm -rf $HOME/.config/nvim/.git
fi

if [ -f "requirements.txt" ]; then
    echo "Installing Python dependencies..."
    mise x python -- pip install --upgrade pip
    mise x python -- pip install -r requirements.txt
fi

echo "Setup complete!"