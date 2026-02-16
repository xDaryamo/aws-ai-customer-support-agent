resource "aws_db_subnet_group" "this" {
  name       = "customer-support-db-subnet-group"
  subnet_ids = var.private_subnets

  tags = {
    Name = "CustomerSupportDBSubnetGroup"
  }
}

resource "aws_security_group" "rds" {
  name        = "customer-support-rds-sg"
  description = "Allow inbound traffic from EC2 to RDS"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [var.ec2_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_instance" "this" {
  allocated_storage      = 20
  engine                 = "mysql"
  engine_version         = "8.0"
  instance_class         = "db.t3.micro"
  db_name                = "customer_inquiry_db"
  username               = "admin"
  password               = var.db_password
  parameter_group_name   = "default.mysql8.0"
  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  skip_final_snapshot    = true
  publicly_accessible    = false

  tags = {
    Name = "CustomerSupportRDS"
  }
}
