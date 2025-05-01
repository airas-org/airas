FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    git \
    curl \
    vim \
    build-essential \
    texlive-base \
    texlive-latex-recommended \
    texlive-fonts-recommended \
    texlive-latex-extra \
    texlive-science \
    chktex \
    locales && \
    rm -rf /var/lib/apt/lists/*

RUN locale-gen en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

RUN curl -LsSf https://astral.sh/uv/install.sh | sh || exit 1
ENV PATH="/root/.uv/bin:$PATH"
RUN bash -lc '\
    uv python install 3.10 && \
    uv python install 3.11 && \
    uv python install 3.12 && \
    uv python install 3.13 && \
    uv python install 3.14 \
'

RUN bash -lc 'uv python pin 3.10'
RUN bash -lc 'uv venv create'

RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get update && apt-get install -y nodejs && \
    npm install -g yarn
