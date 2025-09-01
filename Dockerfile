FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:1
ENV VNC_PORT=5901
ENV NOVNC_PORT=6080
ENV VNC_PASSWORD=mt4vnc
ENV WINE_MONO_VERSION=7.4.0
ENV WINE_GECKO_VERSION=2.47.3
ENV PYTHONUNBUFFERED=1

# Install required packages
RUN apt-get update && apt-get install -y \
    wget \
    software-properties-common \
    gnupg2 \
    xvfb \
    x11vnc \
    novnc \
    websockify \
    supervisor \
    fluxbox \
    xterm \
    net-tools \
    curl \
    vim \
    python3 \
    python3-dev \
    git \
    build-essential \
    && dpkg --add-architecture i386 \
    && wget -qO- https://dl.winehq.org/wine-builds/winehq.key | apt-key add - \
    && add-apt-repository 'deb https://dl.winehq.org/wine-builds/ubuntu/ jammy main' \
    && apt-get update \
    && apt-get install -y --install-recommends winehq-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user with specific UID/GID for consistency
ARG USER_ID=1000
ARG GROUP_ID=1000
ARG USERNAME=developer

RUN groupadd -g ${GROUP_ID} ${USERNAME} \
    && useradd -m -u ${USER_ID} -g ${GROUP_ID} -s /bin/bash ${USERNAME} \
    && echo "${USERNAME}:${USERNAME}" | chpasswd

# Setup VNC password
RUN mkdir -p /home/${USERNAME}/.vnc \
    && x11vnc -storepasswd ${VNC_PASSWORD} /home/${USERNAME}/.vnc/passwd \
    && chown -R ${USERNAME}:${USERNAME} /home/${USERNAME}/.vnc

# Setup noVNC
RUN ln -s /usr/share/novnc/vnc.html /usr/share/novnc/index.html

# Create application directories
RUN mkdir -p /app/converter \
    && mkdir -p /app/mt4-terminal \
    && mkdir -p /app/logs \
    && mkdir -p /app/data \
    && chown -R ${USERNAME}:${USERNAME} /app

# Copy application files
WORKDIR /app/converter
COPY --chown=${USER_ID}:${GROUP_ID} . .

# Install uv package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Install Python dependencies
COPY pyproject.toml /app/converter/
COPY --chown=${USER_ID}:${GROUP_ID} src /app/converter/src/
RUN cd /app/converter && \
    uv venv .venv && \
    . .venv/bin/activate && \
    uv pip install -e . && \
    chown -R ${USERNAME}:${USERNAME} .venv

# Set Python environment
ENV PATH="/app/converter/.venv/bin:$PATH"
ENV VIRTUAL_ENV=/app/converter/.venv

# Copy configuration files
COPY --chown=${USER_ID}:${GROUP_ID} startup.sh /app/
RUN chmod +x /app/startup.sh

# Copy supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/

# Create Wine prefix and install MT4
USER ${USERNAME}
RUN winecfg -v win10 \
    && wineboot --init \
    && mkdir -p /home/${USERNAME}/.wine/drive_c/Program\ Files\ \(x86\)/

# Expose ports
EXPOSE ${VNC_PORT}
EXPOSE ${NOVNC_PORT}
EXPOSE 8000
EXPOSE 9090

# Run as non-root user
USER ${USERNAME}

# Start supervisor as non-root
CMD ["/bin/bash", "-c", "/usr/bin/supervisord -n -c /etc/supervisor/supervisord.conf"]