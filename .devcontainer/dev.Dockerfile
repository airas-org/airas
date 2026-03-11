FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive
ARG USERNAME=developer
ARG USER_UID=1000
ARG USER_GID=1000

RUN apt-get update && apt-get install -y \
    bash git curl vim lsof build-essential locales tmux sudo \
    ca-certificates gnupg \
    && locale-gen en_US.UTF-8 \
    && update-locale LANG=en_US.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Railway CLI
RUN npm install -g @railway/cli

# ttyd / cloudflared
RUN DPKG_ARCH=$(dpkg --print-architecture) && \
    if [ "$DPKG_ARCH" = "amd64" ]; then TTYD_ARCH="x86_64"; else TTYD_ARCH="aarch64"; fi && \
    curl -fsSL -o /usr/local/bin/ttyd \
      "https://github.com/tsl0922/ttyd/releases/download/1.7.7/ttyd.${TTYD_ARCH}" && \
    chmod +x /usr/local/bin/ttyd

RUN ARCH=$(dpkg --print-architecture) && \
    curl -fsSL -o /usr/local/bin/cloudflared \
      "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${ARCH}" && \
    chmod +x /usr/local/bin/cloudflared

# uv・Claude Code
USER $USERNAME
WORKDIR /home/$USERNAME

RUN curl -LsSf https://astral.sh/uv/0.7.2/install.sh | sh

RUN curl -fsSL https://claude.ai/install.sh | bash

ENV PATH="/home/$USERNAME/.uv/bin:/home/$USERNAME/.claude/bin:$PATH"

CMD [ "bash" ]
