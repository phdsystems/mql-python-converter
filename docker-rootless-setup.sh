#!/bin/bash
# Setup Docker rootless mode to avoid sudo requirement
dockerd-rootless-setuptool.sh install

# Add to bashrc for permanent setup
echo 'export PATH=/usr/bin:$PATH' >> ~/.bashrc
echo 'export DOCKER_HOST=unix:///run/user/$(id -u)/docker.sock' >> ~/.bashrc
