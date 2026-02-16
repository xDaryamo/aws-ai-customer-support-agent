output "ec2_public_ip" {
  value = module.compute.instance_public_ip
}

output "rds_endpoint" {
  value = module.rds.db_endpoint
}
