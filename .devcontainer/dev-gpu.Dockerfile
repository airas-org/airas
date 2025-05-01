FROM nvidia/cuda:12.6.3-cudnn-devel-ubuntu20.04

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
    nvidia-container-toolkit \
    locales && \
    rm -rf /var/lib/apt/lists/*

RUN locale-gen en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

RUN curl -LsSf https://astral.sh/uv/0.5.5/install.sh | bash || exit 1

ENV PATH="/root/.uv/bin:$PATH"

RUN bash -lc 'uv python install 3.10'
