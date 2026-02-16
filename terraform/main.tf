module "vpc" {
  source   = "./modules/vpc"
  vpc_cidr = var.vpc_cidr
}

module "compute" {
  source           = "./modules/compute"
  vpc_id           = module.vpc.vpc_id
  public_subnet_id = module.vpc.public_subnets[0]
  my_ip            = var.my_ip
}

module "rds" {
  source                = "./modules/rds"
  vpc_id                = module.vpc.vpc_id
  private_subnets       = module.vpc.private_subnets
  ec2_security_group_id = module.compute.ec2_security_group_id
  db_password           = var.db_password
}
