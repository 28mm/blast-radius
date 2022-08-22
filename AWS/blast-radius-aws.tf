terraform {
}

provider "aws" {
  # uncomment if global configuration is not set up yet
#   access_key = var.AWS_ACCESS_KEY_ID
#   secret_key = var.AWS_SECRET_ACCESS_KEY
   region     = var.AWS_REGION
}

#variable "AWS_ACCESS_KEY_ID" {
#  default = ""
#}
#
#variable "AWS_SECRET_ACCESS_KEY" {
#  default = ""
#}
#
variable "AWS_REGION" {
  default = ""
}

variable "AMI_ID" {
  default = "09d56f8956ab235b3" #UBUNTU
}

variable "KEY_NAME" {
  default = ""
}

variable "KEY_PATH" {
  default = ""
}

variable "ACCESS_PORT" {
  default = 8888
}

resource "aws_vpc" "terraform-vpc" {
  cidr_block       = "10.10.0.0/16"

  tags = {
    Name = "blastradius"
  }
}

resource "aws_subnet" "first-subnet" {
  cidr_block = "10.10.1.0/24"
  vpc_id     = aws_vpc.terraform-vpc.id
  availability_zone = "${var.AWS_REGION}a"
}

resource "aws_route_table" "route-table" {
  vpc_id = aws_vpc.terraform-vpc.id
  tags = {
    Name = "route-table"
  }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.terraform-vpc.id

  tags = {
    Name = "internet-gateway"
  }
}

resource "aws_route" "blast-radius-route" {
  route_table_id         = aws_route_table.route-table.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.igw.id
  depends_on = [
    aws_route_table.route-table,
    aws_internet_gateway.igw
  ]
}

resource "aws_main_route_table_association" "main-rt" {
  vpc_id         = aws_vpc.terraform-vpc.id
  route_table_id = aws_route_table.route-table.id
}

locals {
  rulesmap = {
    "HTTP" = {
      port        = 80,
      cidr_blocks = ["0.0.0.0/0"],
      ipv6_cidr_blocks = ["::/0"]
    },
    "HTTPS" = {
      port        = 443,
      cidr_blocks = ["0.0.0.0/0"],
      ipv6_cidr_blocks = ["::/0"]
    }
    "SSH" = {
      port        = 22,
      cidr_blocks = ["0.0.0.0/0"],
      ipv6_cidr_blocks = ["::/0"]
    },
    "BLASTR" = {
      port        = var.ACCESS_PORT,
      cidr_blocks = ["0.0.0.0/0"],
      ipv6_cidr_blocks = ["::/0"]
    }
  }
}

resource "aws_security_group" "sg" {
  vpc_id = aws_subnet.first-subnet.vpc_id

  dynamic "ingress" {
    for_each = local.rulesmap
    content {
      description = ingress.key # HTTP or SSH
      from_port   = ingress.value.port
      to_port     = ingress.value.port
      protocol    = "tcp"
      cidr_blocks = ingress.value.cidr_blocks
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  egress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name = "default"
  }
}

resource "aws_instance" "blast-radius-ec2-instance" {
  associate_public_ip_address = true
  # ami                         = "ami-02584c1c9d05efa69" // Ubuntu 20.04LTS - not using data.aws_ami.amazon_linux.id
  ami                         = "ami-${var.AMI_ID}"
  instance_type               = "t2.micro"
  key_name                    = "${var.KEY_NAME}"
  vpc_security_group_ids      = [aws_security_group.sg.id]
  subnet_id                   = aws_subnet.first-subnet.id

  connection {
    agent       = false
    host        = self.public_ip
    private_key = file(var.KEY_PATH)
    type        = "ssh"
    user        = "ubuntu"
  }

   provisioner "remote-exec" {
     inline = [
       "sudo apt-get update -y",
       "sudo apt-get install docker.io docker -y",
       "sudo chmod 666 /var/run/docker.sock",
       "sudo service docker start",
        "docker run --rm -it -d -p ${var.ACCESS_PORT}:5000 -v $(pwd):/data:ro --security-opt apparmor:unconfined --cap-add=SYS_ADMIN ianyliu/blast-radius-fork"
     ]
   }

  tags = {
    Terraform   = "true"
    Environment = "dev"
    Name        = "blast-radius"
  }
}

output "ec1-public-ip" {
  value = aws_instance.blast-radius-ec2-instance.public_ip
}

output "port" {
  value = var.ACCESS_PORT
}
