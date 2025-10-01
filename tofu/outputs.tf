output "user_names" {
  description = "The names of the created IAM users."
  value = [for user in values(aws_iam_user.user) : user.name]
}

output "user_access_keys" {
  description = "The access keys for the created IAM users."
  value = {
    for user, key in aws_iam_access_key.user_key :
    user => {
      access_key_id     = key.id
      secret_access_key = key.secret
    }
  }
  sensitive = true
}
