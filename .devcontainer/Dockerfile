FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    build-essential \
    curl \
    git \
    unzip \
    ripgrep \
    fd-find \
    xclip \
    tmux \
    jq \
    && ln -s $(which fdfind) /usr/local/bin/fd \
    && curl -sSL https://raw.githubusercontent.com/alacritty/alacritty/master/extra/alacritty.info | tic -x - \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*


COPY --from=jdxcode/mise:latest /usr/local/bin/mise /usr/local/bin/mise

USER vscode
ENV HOME=/home/vscode

RUN echo 'eval "$(mise activate bash)"' >> $HOME/.bashrc \
    && echo 'source /usr/share/bash-completion/bash_completion' >> $HOME/.bashrc

RUN echo 'eval "$(mise activate zsh)"' >> $HOME/.zshrc


RUN mkdir -p $HOME/.config/nvim

WORKDIR /workspaces/aws-ai-customer-support-agent
