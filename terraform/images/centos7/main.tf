/* ==================================
   Main file for the Local EGA images
   ================================== */

terraform {
  backend "local" {
    path = ".terraform/ega-images.tfstate"
  }
}

# Configure the OpenStack Provider
provider "openstack" {
  user_name   = "s4800"
  password    = "Alaiks3S"
  tenant_id   = "e62c28337a094ea99571adfb0b97939f"
  tenant_name = "SNIC 2017/13-34"
  auth_url    = "https://hpc2n.cloud.snic.se:5000/v3"
  region      = "HPC2N"
  domain_name = "snic"
}

resource "openstack_compute_keypair_v2" "ega_key" {
  name       = "ega-key"
  public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCcLiS1a/+ul3LOGsBvprYLk1a8XYx6isqkVXQ05PlPLOOs83Qv9aN+uh8YOaebPYK3qlXEH4Tbmk/WJTgJJVkhefNZK+Stk3Pkk6oUqwHfZ7+lDWCqP7/Cvm4+HvVsAO+HBhv/8AhKxk6AI7X0ongrWhJLLJDuraFEYmswKAJOWiuxyKM9EbmmAhocKEx9cUHxnj8Rr3EGJ9urCwQxAIclZUfB5SqHQaGv6ApmVs5S2x6F3RG6upx6eXop4h357psaH7HTi90u6aLEjNf3uYdoCyh8AphqZ6NDVamUCXciO+1jKV03gDBC7xuLCk4ZCF0uRMXoFTmmr77AL33LuysL fred@snic-cloud"
}

# ========= Instances =========

resource "openstack_compute_instance_v2" "common" {
  name            = "ega-common"
  flavor_name     = "ssc.small"
  image_name      = "CentOS 7 - latest"
  key_pair        = "${openstack_compute_keypair_v2.ega_key.name}"
  security_groups = ["default"]
  network { name  = "SNIC 2017/13-34 Internal IPv4 Network" }
  user_data       = "${file("${path.module}/common.sh")}"
}

resource "openstack_compute_instance_v2" "db" {
  name            = "ega-db"
  flavor_name     = "ssc.small"
  image_name      = "CentOS 7 - latest"
  key_pair        = "${openstack_compute_keypair_v2.ega_key.name}"
  security_groups = ["default"]
  network { name  = "SNIC 2017/13-34 Internal IPv4 Network" }
  user_data       = "${file("${path.module}/db.sh")}"
}

resource "openstack_compute_instance_v2" "mq" {
  name            = "ega-mq"
  flavor_name     = "ssc.small"
  image_name      = "CentOS 7 - latest"
  key_pair        = "${openstack_compute_keypair_v2.ega_key.name}"
  security_groups = ["default"]
  network { name  = "SNIC 2017/13-34 Internal IPv4 Network" }
  user_data       = "${file("${path.module}/mq.sh")}"
}

resource "openstack_compute_instance_v2" "cega" {
  name            = "cega"
  flavor_name     = "ssc.small"
  image_name      = "CentOS 7 - latest"
  key_pair        = "${openstack_compute_keypair_v2.ega_key.name}"
  security_groups = ["default"]
  network { name  = "SNIC 2017/13-34 Internal IPv4 Network" }
  user_data       = "${file("${path.module}/cega.sh")}"
}
