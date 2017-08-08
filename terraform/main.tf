/* ===================================
   Main file for the Local EGA project
   =================================== */


# Configure the OpenStack Provider
provider "openstack" {
  user_name   = "${var.os_username}"
  password    = "${var.os_password}"
  tenant_id   = "e62c28337a094ea99571adfb0b97939f"
  tenant_name = "SNIC 2017/13-34"
  auth_url    = "https://hpc2n.cloud.snic.se:5000/v3"
  region      = "HPC2N"
  domain_name = "snic"
}

# ========= Key Pair =========
resource "openstack_compute_keypair_v2" "ega_key" {
  name      = "ega_key"
  public_key = "${var.pubkey}"
}

# ========= Network =========
resource "openstack_compute_secgroup_v2" "ega" {
  name        = "ega"
  description = "Rule for the EGA security group"

  rule {
    from_port   = 22
    to_port     = 22
    ip_protocol = "tcp"
    cidr        = "0.0.0.0/0"
  }
  rule {
    from_port   = 80
    to_port     = 80
    ip_protocol = "tcp"
    cidr        = "0.0.0.0/0"
  }
}

resource "openstack_networking_floatingip_v2" "frontend_ip" {
  pool = "public"
}
resource "openstack_networking_floatingip_v2" "inbox_ip" {
  pool = "public"
}

# ========= Volumes =========
resource "openstack_blockstorage_volume_v2" "staging" {
  name = "staging"
  description = "Inbox and Staging area"
  size = 100
}

resource "openstack_blockstorage_volume_v2" "vault" {
  name = "vault"
  description = "Da vault"
  size = 100
}

# ========= Instances =========
# resource "openstack_compute_instance_v2" "frontend" {
#   name      = "frontend"
#   image_name  = "EGA"
#   flavor_name = "ssc.small"
#   key_pair  = "${openstack_compute_keypair_v2.ega_key.name}"
#   security_groups = ["default"]

#   network { name = "${var.ega_net}" }
# }
# resource "openstack_compute_floatingip_associate_v2" "frontend_fip" {
#   floating_ip  = "${openstack_networking_floatingip_v2.frontend_ip.address}"
#   instance_id = "${openstack_compute_instance_v2.frontend.id}"
# }

resource "openstack_compute_instance_v2" "inbox" {
  name      = "inbox"
  image_name  = "EGA"
  flavor_name = "ssc.small"
  key_pair  = "${openstack_compute_keypair_v2.ega_key.name}"
  security_groups = ["default"]

  network { name = "${var.ega_net}" }
}
resource "openstack_compute_floatingip_associate_v2" "inbox_fip" {
  floating_ip  = "${openstack_networking_floatingip_v2.inbox_ip.address}"
  instance_id = "${openstack_compute_instance_v2.inbox.id}"
}
resource "openstack_compute_volume_attach_v2" "inbox_attach" {
  instance_id = "${openstack_compute_instance_v2.inbox.id}"
  volume_id   = "${openstack_blockstorage_volume_v2.staging.id}"
}


# resource "openstack_compute_instance_v2" "vault" {
#   name      = "vault"
#   image_name  = "EGA"
#   flavor_name = "ssc.small"
#   key_pair  = "${openstack_compute_keypair_v2.ega_key.name}"
#   security_groups = ["default"]

#   network { name = "${var.ega_net}" }
# }
# resource "openstack_compute_volume_attach_v2" "vault_attach" {
#   instance_id = "${openstack_compute_instance_v2.vault.id}"
#   volume_id   = "${openstack_blockstorage_volume_v2.vault.id}"
# }

# resource "openstack_compute_instance_v2" "worker" {
#   count     = "${var.workers}"
#   name      = "${format("worker-%02d", count.index+1)}"
#   image_name  = "EGA"
#   flavor_name = "ssc.small"
#   key_pair  = "${openstack_compute_keypair_v2.ega_key.name}"

#   network { name = "${var.ega_net}" }
# }
