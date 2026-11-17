output "instance_id" {
  description = "SupplyChainX EC2 instance ID"
  value       = aws_instance.supplychainx.id
}

output "public_ip" {
  description = "Public IP address of SupplyChainX"
  value       = aws_instance.supplychainx.public_ip
}

output "application_url" {
  description = "SupplyChainX application URL"
  value       = "http://${aws_instance.supplychainx.public_ip}:8000"
}

output "ssm_instance_profile" {
  description = "IAM instance profile attached to EC2"
  value       = aws_instance.supplychainx.iam_instance_profile
}
