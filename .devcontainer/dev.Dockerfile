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

ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

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

ARG CLOUDFLARED_VERSION=2025.1.0
RUN ARCH=$(dpkg --print-architecture) && \
    cd /tmp && \
    curl -fsSL -o "cloudflared-linux-${ARCH}" \
      "https://github.com/cloudflare/cloudflared/releases/download/${CLOUDFLARED_VERSION}/cloudflared-linux-${ARCH}" && \
    curl -fsSL -o "cloudflared-linux-${ARCH}.sha256" \
      "https://github.com/cloudflare/cloudflared/releases/download/${CLOUDFLARED_VERSION}/cloudflared-linux-${ARCH}.sha256" && \
    echo "$(cat cloudflared-linux-${ARCH}.sha256)  cloudflared-linux-${ARCH}" | sha256sum -c - && \
    install -m 0755 "cloudflared-linux-${ARCH}" /usr/local/bin/cloudflared && \
    rm "cloudflared-linux-${ARCH}" "cloudflared-linux-${ARCH}.sha256"

# uv・Claude Code
USER $USERNAME
WORKDIR /home/$USERNAME

RUN curl -LsSf https://astral.sh/uv/0.7.2/install.sh | sh

RUN curl -fsSL https://claude.ai/install.sh | bash

ENV PATH="/home/$USERNAME/.uv/bin:/home/$USERNAME/.claude/bin:$PATH"

CMD [ "bash" ]
