#!/bin/bash
set -eux

dnf update -y

# Install Docker and SSM Agent
dnf install -y docker amazon-ssm-agent

# Start Docker
systemctl enable docker
systemctl start docker

# Start Systems Manager Agent
systemctl enable amazon-ssm-agent
systemctl start amazon-ssm-agent

# Install Docker Compose plugin
mkdir -p /usr/local/lib/docker/cli-plugins

curl -SL \
  https://github.com/docker/compose/releases/download/v2.29.7/docker-compose-linux-x86_64 \
  -o /usr/local/lib/docker/cli-plugins/docker-compose

chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# Prepare application directory
mkdir -p /opt/supplychainx
chown ec2-user:ec2-user /opt/supplychainx

echo "SupplyChainX EC2 initialization completed"
