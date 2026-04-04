variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "ai-healing-platform"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "ami_id" {
  description = "Ubuntu 22.04 LTS AMI ID for us-east-1"
  type        = string
  default     = "ami-0e86e20dae9224db8"  # Ubuntu 22.04 LTS in us-east-1
}

variable "master_instance_type" {
  description = "EC2 instance type for master node"
  type        = string
  default     = "t3.small"  # 2GB RAM required for k3s + Prometheus
}

variable "worker_instance_type" {
  description = "EC2 instance type for worker node"
  type        = string
  default     = "t3.micro"  # Free tier eligible
}

variable "k3s_token" {
  description = "Shared secret for k3s cluster (auto-generated if not provided)"
  type        = string
  default     = "mtech-ai-healing-k3s-secret-token-2026"
  sensitive   = true
}

variable "ssh_public_key_path" {
  description = "Path to SSH public key for EC2 instances"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

variable "ssh_private_key_path" {
  description = "Path to SSH private key for provisioning"
  type        = string
  default     = "~/.ssh/id_rsa"
}
