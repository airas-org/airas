FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    bash \
    git \
    curl \
    vim \
    lsof \
    build-essential \
    locales \
    tmux \
    && locale-gen en_US.UTF-8 && \
    update-locale LANG=en_US.UTF-8 && \
    rm -rf /var/lib/apt/lists/*

ENV LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8 \
    PATH="/root/.uv/bin:$PATH"

# Backend
RUN curl -LsSf https://astral.sh/uv/0.7.2/install.sh | sh

## Frontend & Docs
RUN apt-get install -y curl ca-certificates gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# ttyd (web terminal)
RUN DPKG_ARCH=$(dpkg --print-architecture) && \
    if [ "$DPKG_ARCH" = "amd64" ]; then TTYD_ARCH="x86_64"; else TTYD_ARCH="aarch64"; fi && \
    curl -fsSL -o /usr/local/bin/ttyd \
      "https://github.com/tsl0922/ttyd/releases/download/1.7.7/ttyd.${TTYD_ARCH}" && \
    chmod +x /usr/local/bin/ttyd

# cloudflared (Cloudflare Tunnel)
RUN ARCH=$(dpkg --print-architecture) && \
    curl -fsSL -o /usr/local/bin/cloudflared \
      "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${ARCH}" && \
    chmod +x /usr/local/bin/cloudflared

# Claude Code
RUN curl -fsSL https://claude.ai/install.sh | bash

CMD [ "bash" ]
