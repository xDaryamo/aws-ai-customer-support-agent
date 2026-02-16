variable "vpc_id" {
  type = string
}

variable "public_subnet_id" {
  type = string
}

variable "my_ip" {
  description = "Allowed IP for SSH access"
  type        = string
}
