# Terraform Configuration for AI Self-Healing Platform on AWS Free Tier
# Provider: AWS (Free tier: 2x t3.micro for 12 months)
# Kubernetes: k3s (lightweight)
# Cost: $0/month for first year

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "AI-Self-Healing-Platform"
      Environment = "Demo"
      ManagedBy   = "Terraform"
      Student     = "MTech-Project"
    }
  }
}

# ============================================================================
# VARIABLES
# ============================================================================

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "cluster_name" {
  description = "Cluster name"
  type        = string
  default     = "ai-healing-cluster"
}

variable "key_name" {
  description = "SSH key pair name (must exist in AWS)"
  type        = string
  default     = "mtech-project-key"
}

variable "instance_type" {
  description = "EC2 instance type (t3.micro is free tier)"
  type        = string
  default     = "t3.micro"
}

variable "allowed_ssh_cidr" {
  description = "CIDR block allowed to SSH (use your IP/32 for security)"
  type        = string
  default     = "0.0.0.0/0"  # Change to your IP for production
}

# ============================================================================
# DATA SOURCES
# ============================================================================

# Get latest Ubuntu 22.04 AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]  # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Get availability zones
data "aws_availability_zones" "available" {
  state = "available"
}

# ============================================================================
# VPC & NETWORKING
# ============================================================================

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.cluster_name}-vpc"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.cluster_name}-igw"
  }
}

resource "aws_subnet" "public_1" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.cluster_name}-public-subnet-1"
  }
}

resource "aws_subnet" "public_2" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = data.aws_availability_zones.available.names[1]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.cluster_name}-public-subnet-2"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${var.cluster_name}-public-rt"
  }
}

resource "aws_route_table_association" "public_1" {
  subnet_id      = aws_subnet.public_1.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_2" {
  subnet_id      = aws_subnet.public_2.id
  route_table_id = aws_route_table.public.id
}

# ============================================================================
# SECURITY GROUPS
# ============================================================================

resource "aws_security_group" "k3s_cluster" {
  name        = "${var.cluster_name}-sg"
  description = "Security group for k3s cluster"
  vpc_id      = aws_vpc.main.id

  # SSH access
  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
  }

  # k3s API server
  ingress {
    description = "k3s API"
    from_port   = 6443
    to_port     = 6443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTP
  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS
  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # NodePort range
  ingress {
    description = "NodePort Services"
    from_port   = 30000
    to_port     = 32767
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Prometheus
  ingress {
    description = "Prometheus"
    from_port   = 30090
    to_port     = 30090
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow all internal traffic
  ingress {
    description = "Internal cluster traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    self        = true
  }

  # Allow all outbound
  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.cluster_name}-sg"
  }
}

# ============================================================================
# EC2 INSTANCES
# ============================================================================

# Master Node
resource "aws_instance" "master" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = var.key_name
  subnet_id              = aws_subnet.public_1.id
  vpc_security_group_ids = [aws_security_group.k3s_cluster.id]

  root_block_device {
    volume_size = 30  # Free tier: 30GB
    volume_type = "gp3"
  }

  user_data = templatefile("${path.module}/scripts/master-init.sh", {
    cluster_name = var.cluster_name
  })

  tags = {
    Name = "${var.cluster_name}-master"
    Role = "master"
  }
}

# Worker Node
resource "aws_instance" "worker" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = var.key_name
  subnet_id              = aws_subnet.public_2.id
  vpc_security_group_ids = [aws_security_group.k3s_cluster.id]

  root_block_device {
    volume_size = 30
    volume_type = "gp3"
  }

  user_data = templatefile("${path.module}/scripts/worker-init.sh", {
    master_private_ip = aws_instance.master.private_ip
  })

  depends_on = [aws_instance.master]

  tags = {
    Name = "${var.cluster_name}-worker"
    Role = "worker"
  }
}

# ============================================================================
# OUTPUTS
# ============================================================================

output "cluster_info" {
  description = "Cluster connection information"
  value = {
    master_public_ip  = aws_instance.master.public_ip
    master_private_ip = aws_instance.master.private_ip
    worker_public_ip  = aws_instance.worker.public_ip
    worker_private_ip = aws_instance.worker.private_ip
    vpc_id            = aws_vpc.main.id
    security_group_id = aws_security_group.k3s_cluster.id
  }
}

output "ssh_commands" {
  description = "SSH connection commands"
  value = {
    master = "ssh -i ~/.ssh/${var.key_name}.pem ubuntu@${aws_instance.master.public_ip}"
    worker = "ssh -i ~/.ssh/${var.key_name}.pem ubuntu@${aws_instance.worker.public_ip}"
  }
}

output "kubeconfig_command" {
  description = "Command to get kubeconfig"
  value       = "scp -i ~/.ssh/${var.key_name}.pem ubuntu@${aws_instance.master.public_ip}:/etc/rancher/k3s/k3s.yaml ~/.kube/aws-config"
}

output "dashboard_url" {
  description = "Dashboard URL (after deployment)"
  value       = "http://${aws_instance.master.public_ip}:30888"
}

output "prometheus_url" {
  description = "Prometheus URL"
  value       = "http://${aws_instance.master.public_ip}:30090"
}

output "estimated_monthly_cost" {
  description = "Estimated monthly cost"
  value       = "FREE (first 12 months with AWS Free Tier)"
}
