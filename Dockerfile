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

# Create user for Wine
RUN useradd -m -s /bin/bash wineuser \
    && echo "wineuser:wineuser" | chpasswd

# Setup VNC password
RUN mkdir -p /home/wineuser/.vnc \
    && x11vnc -storepasswd ${VNC_PASSWORD} /home/wineuser/.vnc/passwd \
    && chown -R wineuser:wineuser /home/wineuser/.vnc

# Setup noVNC
RUN ln -s /usr/share/novnc/vnc.html /usr/share/novnc/index.html

# Create application directories
RUN mkdir -p /app/converter \
    && mkdir -p /app/mt4-terminal \
    && mkdir -p /app/logs \
    && mkdir -p /app/data \
    && chown -R wineuser:wineuser /app

# Copy application files
WORKDIR /app/converter
COPY --chown=wineuser:wineuser . .

# Install uv package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Install Python dependencies
COPY pyproject.toml /app/converter/
COPY --chown=wineuser:wineuser src /app/converter/src/
RUN cd /app/converter && \
    uv venv .venv && \
    . .venv/bin/activate && \
    uv pip install -e . && \
    chown -R wineuser:wineuser .venv

# Set Python environment
ENV PATH="/app/converter/.venv/bin:$PATH"
ENV VIRTUAL_ENV=/app/converter/.venv

# Copy configuration files
COPY --chown=wineuser:wineuser startup.sh /app/
RUN chmod +x /app/startup.sh

# Copy supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/

# Create Wine prefix and install MT4
USER wineuser
RUN winecfg -v win10 \
    && wineboot --init \
    && mkdir -p /home/wineuser/.wine/drive_c/Program\ Files\ \(x86\)/

# Switch back to root for supervisor
USER root

# Expose ports
EXPOSE ${VNC_PORT}
EXPOSE ${NOVNC_PORT}
EXPOSE 8000
EXPOSE 9090

# Start supervisor
CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/supervisord.conf"]