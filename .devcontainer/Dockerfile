FROM mcr.microsoft.com/devcontainers/base:ubuntu-22.04

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    make \
    openmpi-bin \
    libopenmpi-dev \
  && rm -rf /var/lib/apt/lists/*

ENV DEBIAN_FRONTEND=noninteractive

CMD ["sleep", "infinity"]
