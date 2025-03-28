# Используем легковесный базовый образ Debian Bookworm
FROM debian:bookworm-slim AS builder

# Убираем интерактивные запросы при установке пакетов
ENV DEBIAN_FRONTEND=noninteractive

# Устанавливаем необходимые системные зависимости
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

# Устанавливаем Pixi глобально
RUN curl -fsSL https://pixi.sh/install.sh | bash && \
    mv /root/.pixi/bin/pixi /usr/local/bin/pixi && \
    rm -rf /root/.pixi

# Создаем рабочую директорию
WORKDIR /workspace

# Копируем ТОЛЬКО pixi.toml для кеширования установки зависимостей
COPY ../pixi.toml ./pixi.toml

# Устанавливаем зависимости СТРОГО по pixi.toml (без lock файла и флага --frozen)
# Это гарантирует разрешение зависимостей "с нуля" на основе toml файла при каждом изменении toml
# или при чистой сборке
RUN pixi install

# Создаем непривилегированного пользователя vscode
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    # Добавляем пользователя в sudoers (опционально)
    && apt-get update && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем владельца рабочей директории
# Делаем это до копирования остального кода
RUN chown -R $USERNAME:$USER_GID /workspace

# Переключаемся на пользователя vscode
USER $USERNAME

# Копируем остальной код проекта (после установки зависимостей)
# Права уже установлены через chown выше и --chown здесь
COPY --chown=$USERNAME:$USER_GID .. /workspace

# Открываем порт Streamlit
EXPOSE 8501

# Используем задачу 'start' из pixi.toml
CMD ["pixi", "run", "start"]