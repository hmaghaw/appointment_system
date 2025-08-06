#!/bin/bash
sudo dnf update -y
sudo dnf install -y dnf-plugins-core
sudo dnf clean all
sudo dnf install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
newgrp docker

sudo curl -L "https://github.com/docker/compose/releases/download/v2.17.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
# DO NOT do: sudo chmod 666 /var/run/docker.sock  # Avoid this for security reasons
docker-compose --version