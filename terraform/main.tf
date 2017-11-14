/* ===================================
   Main file for the Local EGA project
   =================================== */

variable os_username {}
variable os_password {}
variable tenant_id {}
variable tenant_name {}
variable auth_url {}
variable region {}
variable domain_name {}
variable router_id {}
variable dns_servers { type = list }

terraform {
  backend "local" {
    path = ".terraform/ega.tfstate"
  }
}

# Configure the OpenStack Provider
provider "openstack" {
  user_name   = "${var.os_username}"
  password    = "${var.os_password}"
  tenant_id   = "${var.tenant_id}"
  tenant_name = "${var.tenant_name}"
  auth_url    = "${var.auth_url}"
  region      = "${var.region}"
  domain_name = "${var.domain_name}"
}

module "cega" {
  source = "./cega"
  private_ip  = "192.168.100.100"
  cega_data = "bootstrap/../private/cega"
  pubkey = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCcLiS1a/+ul3LOGsBvprYLk1a8XYx6isqkVXQ05PlPLOOs83Qv9aN+uh8YOaebPYK3qlXEH4Tbmk/WJTgJJVkhefNZK+Stk3Pkk6oUqwHfZ7+lDWCqP7/Cvm4+HvVsAO+HBhv/8AhKxk6AI7X0ongrWhJLLJDuraFEYmswKAJOWiuxyKM9EbmmAhocKEx9cUHxnj8Rr3EGJ9urCwQxAIclZUfB5SqHQaGv6ApmVs5S2x6F3RG6upx6eXop4h357psaH7HTi90u6aLEjNf3uYdoCyh8AphqZ6NDVamUCXciO+1jKV03gDBC7xuLCk4ZCF0uRMXoFTmmr77AL33LuysL fred@snic-cloud"
  cidr = "192.168.100.0/24"
  dns_servers = ${var.dns_servers}
  router_id = "${var.router_id}"
}

module "instance_fin1" {
       source = "./instance"
       instance = "fin1"
       instance_data = "bootstrap/../private/fin1"
       pubkey = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCcLiS1a/+ul3LOGsBvprYLk1a8XYx6isqkVXQ05PlPLOOs83Qv9aN+uh8YOaebPYK3qlXEH4Tbmk/WJTgJJVkhefNZK+Stk3Pkk6oUqwHfZ7+lDWCqP7/Cvm4+HvVsAO+HBhv/8AhKxk6AI7X0ongrWhJLLJDuraFEYmswKAJOWiuxyKM9EbmmAhocKEx9cUHxnj8Rr3EGJ9urCwQxAIclZUfB5SqHQaGv6ApmVs5S2x6F3RG6upx6eXop4h357psaH7HTi90u6aLEjNf3uYdoCyh8AphqZ6NDVamUCXciO+1jKV03gDBC7xuLCk4ZCF0uRMXoFTmmr77AL33LuysL fred@snic-cloud"
       cidr = "192.168.40.0/24"
       dns_servers = ${var.dns_servers}
       router_id = "${var.router_id}"

       db_user = "lega"
       db_password = "V1INWEo7c5B5vHYX"
       db_name = "lega"

       ip_db = "192.168.40.10"
       ip_mq = "192.168.40.11"
       ip_inbox = "192.168.40.12"
       ip_frontend = "192.168.40.13"
       ip_monitors = "192.168.40.15"
       ip_vault = "192.168.40.14"
       ip_keys = "192.168.40.16"
       ip_workers = ["192.168.40.101","192.168.40.102"]

       greetings = "Welcome to Local EGA Finland @ CSC"

       inbox_size = "200"
       inbox_path = "/ega/inbox/"
       vault_size = "100"

       gpg_passphrase = "VltxALNWkbXFoygG"
}
module "instance_swe1" {
       source = "./instance"
       instance = "swe1"
       instance_data = "bootstrap/../private/swe1"
       pubkey = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCcLiS1a/+ul3LOGsBvprYLk1a8XYx6isqkVXQ05PlPLOOs83Qv9aN+uh8YOaebPYK3qlXEH4Tbmk/WJTgJJVkhefNZK+Stk3Pkk6oUqwHfZ7+lDWCqP7/Cvm4+HvVsAO+HBhv/8AhKxk6AI7X0ongrWhJLLJDuraFEYmswKAJOWiuxyKM9EbmmAhocKEx9cUHxnj8Rr3EGJ9urCwQxAIclZUfB5SqHQaGv6ApmVs5S2x6F3RG6upx6eXop4h357psaH7HTi90u6aLEjNf3uYdoCyh8AphqZ6NDVamUCXciO+1jKV03gDBC7xuLCk4ZCF0uRMXoFTmmr77AL33LuysL fred@snic-cloud"
       cidr = "192.168.10.0/24"
       dns_servers = ${var.dns_servers}
       router_id = "${var.router_id}"

       db_user = "lega"
       db_password = "HtXfJKUoilFJWnip"
       db_name = "lega"

       ip_db = "192.168.10.10"
       ip_mq = "192.168.10.11"
       ip_inbox = "192.168.10.12"
       ip_frontend = "192.168.10.13"
       ip_monitors = "192.168.10.15"
       ip_vault = "192.168.10.14"
       ip_keys = "192.168.10.16"
       ip_workers = ["192.168.10.101","192.168.10.102","192.168.10.103","192.168.10.104"]

       greetings = "Welcome to Local EGA Sweden @ NBIS"

       inbox_size = "300"
       inbox_path = "/ega/inbox/"
       vault_size = "150"

       gpg_passphrase = "xRZWFQTZLTRhkzeL"
}
