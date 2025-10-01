terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

resource "aws_iam_user" "user" {
  for_each = toset(var.user_names)
  name     = each.value
}

resource "aws_iam_user_policy_attachment" "user_policy_attachment" {
  for_each   = aws_iam_user.user
  user       = each.value.name
  policy_arn = var.policy_arn
}

resource "aws_iam_access_key" "user_key" {
  for_each = aws_iam_user.user
  user    = each.value.name
}
