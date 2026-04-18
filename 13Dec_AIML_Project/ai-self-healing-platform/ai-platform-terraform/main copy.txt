# AI Self-Healing Platform - Complete Production Terraform
# Single Master + Guaranteed Prometheus Installation

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
}

data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = {
    Name    = "${var.project_name}-vpc"
    Project = var.project_name
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags = {
    Name    = "${var.project_name}-igw"
    Project = var.project_name
  }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.0.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true
  tags = {
    Name    = "${var.project_name}-public"
    Project = var.project_name
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  tags = {
    Name    = "${var.project_name}-rt"
    Project = var.project_name
  }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

resource "aws_security_group" "k3s" {
  name        = "${var.project_name}-sg"
  description = "k3s master security group"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 6443
    to_port     = 6443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 30000
    to_port     = 32767
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
    Name    = "${var.project_name}-sg"
    Project = var.project_name
  }
}

resource "aws_key_pair" "cluster_key" {
  key_name   = "${var.project_name}-key"
  public_key = file(var.ssh_public_key_path)
  tags = {
    Name    = "${var.project_name}-key"
    Project = var.project_name
  }
}

resource "aws_instance" "master" {
  ami                    = var.ami_id
  instance_type          = var.master_instance_type
  key_name               = aws_key_pair.cluster_key.key_name
  vpc_security_group_ids = [aws_security_group.k3s.id]
  subnet_id              = aws_subnet.public.id

  root_block_device {
    volume_size = 30
    volume_type = "gp3"
  }

  user_data = templatefile("${path.module}/scripts/master-init.sh", {
    k3s_token = var.k3s_token
  })

  tags = {
    Name    = "${var.project_name}-master"
    Project = var.project_name
  }
}

resource "null_resource" "upload_files" {
  depends_on = [aws_instance.master]

  provisioner "remote-exec" {
    inline = [
      "mkdir -p /home/ubuntu/ai-platform",
      "chmod 755 /home/ubuntu/ai-platform"
    ]
    connection {
      type        = "ssh"
      user        = "ubuntu"
      private_key = file(var.ssh_private_key_path)
      host        = aws_instance.master.public_ip
      timeout     = "5m"
    }
  }

  provisioner "file" {
    source      = "${path.module}/app-files/"
    destination = "/home/ubuntu/ai-platform"
    connection {
      type        = "ssh"
      user        = "ubuntu"
      private_key = file(var.ssh_private_key_path)
      host        = aws_instance.master.public_ip
      timeout     = "10m"
    }
  }

  provisioner "remote-exec" {
    inline = [
      "chown -R ubuntu:ubuntu /home/ubuntu/ai-platform",
      "chmod -R 755 /home/ubuntu/ai-platform"
    ]
    connection {
      type        = "ssh"
      user        = "ubuntu"
      private_key = file(var.ssh_private_key_path)
      host        = aws_instance.master.public_ip
      timeout     = "5m"
    }
  }
}

resource "null_resource" "deploy" {
  depends_on = [null_resource.upload_files]

  provisioner "remote-exec" {
    inline = [
      "echo 'Waiting for k3s...'",
      "timeout 300 bash -c 'until sudo k3s kubectl get nodes | grep -q Ready; do sleep 5; done'",
      "echo 'k3s ready!'",
      "",
      "cd /home/ubuntu/ai-platform",
      "chmod +x scripts/deploy-all.sh",
      "",
      "echo 'Starting deployment...'",
      "bash scripts/deploy-all.sh 2>&1 | tee /tmp/deployment.log",
      "",
      "echo 'Verifying Prometheus...'",
      "export KUBECONFIG=/etc/rancher/k3s/k3s.yaml",
      "",
      "# Check Prometheus",
      "if ! sudo k3s kubectl get svc prometheus-server -n monitoring &>/dev/null; then",
      "  echo 'Prometheus not found, installing...'",
      "  ",
      "  # Install Helm",
      "  if ! command -v helm &> /dev/null; then",
      "    curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash",
      "  fi",
      "  ",
      "  # Install Prometheus",
      "  helm repo add prometheus-community https://prometheus-community.github.io/helm-charts",
      "  helm repo update",
      "  ",
      "  helm install prometheus prometheus-community/prometheus \\",
      "    --namespace monitoring \\",
      "    --set server.service.type=NodePort \\",
      "    --set server.service.nodePort=30090 \\",
      "    --set alertmanager.enabled=false \\",
      "    --set prometheus-pushgateway.enabled=false \\",
      "    --set server.persistentVolume.enabled=false \\",
      "    --set kube-state-metrics.enabled=true \\",
      "    --wait --timeout=5m",
      "  ",
      "  echo 'Prometheus installed'",
      "fi",
      "",
      "# Update AI platform config",
      "sudo k3s kubectl patch configmap ai-platform-config -n monitoring-demo --type=merge -p '{\"data\":{\"PROMETHEUS_ENABLED\":\"true\",\"PROMETHEUS_URL\":\"http://prometheus-server.monitoring.svc.cluster.local\"}}' || true",
      "",
      "# Restart AI platform",
      "sudo k3s kubectl rollout restart deployment/ai-platform -n monitoring-demo",
      "sleep 10",
      "",
      "# Final status",
      "echo ''",
      "echo '========================================'",
      "echo 'DEPLOYMENT COMPLETE'",
      "echo '========================================'",
      "sudo k3s kubectl get nodes",
      "sudo k3s kubectl get pods -n monitoring-demo",
      "sudo k3s kubectl get svc -n monitoring-demo",
      "sudo k3s kubectl get svc -n monitoring | grep prometheus",
      "",
      "MASTER_IP=$(curl -s http://checkip.amazonaws.com)",
      "echo ''",
      "echo 'Dashboard:  http://'$MASTER_IP':30800'",
      "echo 'Sample App: http://'$MASTER_IP':30080/health'",
      "echo 'Prometheus: http://'$MASTER_IP':30090'",
      "echo '========================================'"
    ]

    connection {
      type        = "ssh"
      user        = "ubuntu"
      private_key = file(var.ssh_private_key_path)
      host        = aws_instance.master.public_ip
      timeout     = "25m"
    }
  }

  triggers = {
    always_run = timestamp()
  }
}

output "master_public_ip" {
  value = aws_instance.master.public_ip
}

output "dashboard_url" {
  value = "http://${aws_instance.master.public_ip}:30800"
}

output "sample_app_url" {
  value = "http://${aws_instance.master.public_ip}:30080/health"
}

output "prometheus_url" {
  value = "http://${aws_instance.master.public_ip}:30090"
}

output "ssh_command" {
  value = "ssh -i ${var.ssh_private_key_path} ubuntu@${aws_instance.master.public_ip}"
}

output "deployment_summary" {
  value = <<-EOT
    ================================================================
    AI SELF-HEALING PLATFORM - PRODUCTION READY
    ================================================================
    
    Dashboard:  http://${aws_instance.master.public_ip}:30800
    Sample App: http://${aws_instance.master.public_ip}:30080
    Prometheus: http://${aws_instance.master.public_ip}:30090
    
    SSH: ssh -i ${var.ssh_private_key_path} ubuntu@${aws_instance.master.public_ip}
    
    ================================================================
  EOT
}
