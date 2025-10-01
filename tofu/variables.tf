variable "aws_region" {
  description = "The AWS region to use."
  type        = string
  default     = "us-east-1"
}

variable "user_names" {
  description = "List of IAM user names to create."
  type        = list(string)
  default     = ["hugo-persson", "vivian-tram", "linda-blom", "ludvig-lindholm", "lucas-mansson"]
}

variable "policy_arn" {
  description = "The policy ARN to attach to each user."
  type        = string
  default     = "arn:aws:iam::aws:policy/AmazonSESFullAccess"
}
