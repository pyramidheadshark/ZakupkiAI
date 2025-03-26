FROM debian:bookworm-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        curl \
        ca-certificates \
        git \
        libopenblas-dev \
        liblapack-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://pixi.sh/install.sh | bash

ENV PATH="/root/.pixi/bin:${PATH}"

WORKDIR /workspace

COPY pixi.toml ./pixi.toml

RUN pixi install

ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && apt-get update && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN chown -R $USERNAME:$USER_GID /workspace

RUN mkdir -p /home/$USERNAME/.pixi && chown -R $USERNAME:$USER_GID /home/$USERNAME/.pixi
ENV PATH="/home/${USERNAME}/.pixi/bin:${PATH}"

USER $USERNAME

# COPY --chown=$USERNAME:$USER_GID .. /workspace

EXPOSE 8501

# Используем задачу 'start' из pixi.toml
# CMD ["pixi", "run", "start"]
CMD ["sleep", "infinity"]