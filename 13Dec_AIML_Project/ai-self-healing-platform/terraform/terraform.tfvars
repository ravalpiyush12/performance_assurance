# AWS Region (Free tier available in all regions)
aws_region = "us-east-1"

# Cluster name
cluster_name = "ai-healing-cluster"

# SSH Key name (created in step 1C)
key_name = "mtech-project-key"

# Instance type (FREE TIER)
instance_type = "t3.micro"

# Your public IP for SSH access
# Find it: curl ifconfig.me
allowed_ssh_cidr = "122.170.193.173/32"  # Change to "YOUR_IP/32" for security