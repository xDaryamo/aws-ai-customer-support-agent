variable "vpc_id" {
  type = string
}

variable "private_subnets" {
  type = list(string)
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "ec2_security_group_id" {
  type = string
}
