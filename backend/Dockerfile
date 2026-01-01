FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    curl ca-certificates build-essential \
    && rm -rf /var/lib/apt/lists/*

# uv
ENV PATH="/root/.local/bin:$PATH"
RUN curl -LsSf https://astral.sh/uv/0.7.2/install.sh | sh

WORKDIR /app

COPY pyproject.toml uv.lock* README.md /app/
RUN uv sync --frozen

COPY . /app

EXPOSE 8000

CMD ["bash", "-lc", "uv run uvicorn api.main:app --host 0.0.0.0 --port 8000"]
