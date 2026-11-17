terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Latest Amazon Linux 2023 AMI
data "aws_ssm_parameter" "al2023_ami" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

# Default VPC
data "aws_vpc" "default" {
  default = true
}

# Public subnets in default VPC
data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# Security group: application access only
resource "aws_security_group" "supplychainx_sg" {
  name        = "supplychainx-security-group"
  description = "Allow public access to SupplyChainX application"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SupplyChainX web application"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "SupplyChainX-SecurityGroup"
  }
}

# EC2 application server
resource "aws_instance" "supplychainx" {
  ami                         = data.aws_ssm_parameter.al2023_ami.value
  instance_type               = var.instance_type
  subnet_id                   = data.aws_subnets.default.ids[0]
  associate_public_ip_address = true
  vpc_security_group_ids      = [aws_security_group.supplychainx_sg.id]
  iam_instance_profile        = var.instance_profile_name

  user_data = file("${path.module}/user_data.sh")

  root_block_device {
    volume_size = 8
    volume_type = "gp3"
  }

  tags = {
    Name        = "SupplyChainX-Server"
    Project     = "SupplyChainX"
    Environment = "Academic"
  }
}
