output "master_public_ip" {
  description = "Public IP of master node"
  value       = aws_instance.master.public_ip
}

output "master_private_ip" {
  description = "Private IP of master node"
  value       = aws_instance.master.private_ip
}

output "worker_public_ip" {
  description = "Public IP of worker node"
  value       = aws_instance.worker.public_ip
}

output "worker_private_ip" {
  description = "Private IP of worker node"
  value       = aws_instance.worker.private_ip
}

output "dashboard_url" {
  description = "AI Self-Healing Platform Dashboard URL"
  value       = "http://${aws_instance.master.public_ip}:30800"
}

output "sample_app_url" {
  description = "Sample Application URL"
  value       = "http://${aws_instance.master.public_ip}:30080/health"
}

output "prometheus_url" {
  description = "Prometheus Dashboard URL"
  value       = "http://${aws_instance.master.public_ip}:30090"
}

output "ssh_master_command" {
  description = "SSH command to connect to master"
  value       = "ssh -i ${var.ssh_private_key_path} ubuntu@${aws_instance.master.public_ip}"
}

output "ssh_worker_command" {
  description = "SSH command to connect to worker"
  value       = "ssh -i ${var.ssh_private_key_path} ubuntu@${aws_instance.worker.public_ip}"
}

output "kubectl_command" {
  description = "kubectl command via SSH"
  value       = "ssh -i ${var.ssh_private_key_path} ubuntu@${aws_instance.master.public_ip} 'sudo k3s kubectl'"
}

output "deployment_summary" {
  description = "Complete deployment summary"
  value = <<-EOT
  
  ╔════════════════════════════════════════════════════════════════════╗
  ║     AI SELF-HEALING PLATFORM - DEPLOYMENT COMPLETE!                ║
  ╚════════════════════════════════════════════════════════════════════╝
  
  📊 DASHBOARD ACCESS:
     ${aws_instance.master.public_ip}:30800
  
  🌐 SAMPLE APPLICATION:
     ${aws_instance.master.public_ip}:30080/health
  
  📈 PROMETHEUS:
     ${aws_instance.master.public_ip}:30090
  
  🔐 SSH ACCESS:
     Master: ssh -i ${var.ssh_private_key_path} ubuntu@${aws_instance.master.public_ip}
     Worker: ssh -i ${var.ssh_private_key_path} ubuntu@${aws_instance.worker.public_ip}
  
  ⚙️  KUBECTL (via SSH):
     ssh -i ${var.ssh_private_key_path} ubuntu@${aws_instance.master.public_ip} 'sudo k3s kubectl get pods -A'
  
  🧪 RUN VALIDATION TEST:
     python validate_self_healing.py \\
       --url http://${aws_instance.master.public_ip}:30080 \\
       --ai-platform http://${aws_instance.master.public_ip}:30800 \\
       --scenario cpu
  
  🎯 TRIGGER SELF-HEALING:
     PowerShell: See load-test.ps1
     Or visit dashboard and watch it auto-detect anomalies!
  
  EOT
}
