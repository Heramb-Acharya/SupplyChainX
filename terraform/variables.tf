variable "aws_region" {
  description = "AWS region for SupplyChainX deployment"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
}

variable "instance_profile_name" {
  description = "Existing AWS Academy IAM instance profile"
  type        = string
  default     = "LabInstanceProfile"
}
