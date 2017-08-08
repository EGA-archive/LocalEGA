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

# ========= Security Groups =========
resource "openstack_compute_secgroup_v2" "ega_sftp" {
  name        = "ega-sftp"
  description = "SFTP access"

  rule {
    from_port   = 22
    to_port     = 22
    ip_protocol = "tcp"
    cidr        = "0.0.0.0/0"
  }
}

resource "openstack_compute_secgroup_v2" "ega_web" {
  name        = "ega-web"
  description = "Web access"

  rule {
    from_port   = 80
    to_port     = 80
    ip_protocol = "tcp"
    cidr        = "0.0.0.0/0"
  }
  rule {
    from_port   = 443
    to_port     = 443
    ip_protocol = "tcp"
    cidr        = "0.0.0.0/0"
  }
}

resource "openstack_compute_secgroup_v2" "ega_mq" {
  name        = "ega-mq"
  description = "RabbitMQ access"

  rule {
    from_port   = 5672
    to_port     = 5672
    ip_protocol = "tcp"
    cidr        = "0.0.0.0/0"
  }
  rule {
    from_port   = 15672
    to_port     = 15672
    ip_protocol = "tcp"
    cidr        = "0.0.0.0/0"
  }
}

resource "openstack_compute_secgroup_v2" "ega_db" {
  name        = "ega-db"
  description = "Postgres DB access"

  rule {
    from_port   = 5432
    to_port     = 5432
    ip_protocol = "tcp"
    cidr        = "0.0.0.0/0"
  }
  rule {
    from_port   = 5050
    to_port     = 5050
    ip_protocol = "tcp"
    cidr        = "0.0.0.0/0"
  }
}


# ========= Floating IPs =========
resource "openstack_networking_floatingip_v2" "frontend_ip" {
  pool = "Public External IPv4 Network"
}
resource "openstack_networking_floatingip_v2" "inbox_ip" {
  pool = "Public External IPv4 Network"
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
#   flavor_name = "ssc.small"
#   key_pair  = "${openstack_compute_keypair_v2.ega_key.name}"
#   security_groups = ["default","${openstack_compute_secgroup_v2.ega_web.name}"]
#   #user_data       = "${file("cloud-init/frontend.sh")}"
#   network {
#     name = "${var.ega_net}"
#   }
#   block_device {
#     uuid                  = "${var.ega_common_snapshot_id}"
#     source_type           = "snapshot"
#     volume_size           = 10
#     destination_type      = "volume"
#     boot_index            = 0
#     delete_on_termination = true
#   }
# }
# resource "openstack_compute_floatingip_associate_v2" "frontend_fip" {
#   floating_ip  = "${openstack_networking_floatingip_v2.frontend_ip.address}"
#   instance_id = "${openstack_compute_instance_v2.frontend.id}"
# }

# ===============================
resource "openstack_compute_instance_v2" "inbox" {
  name      = "inbox"
  flavor_name = "ssc.small"
  key_pair  = "${openstack_compute_keypair_v2.ega_key.name}"
  security_groups = ["default","${openstack_compute_secgroup_v2.ega_sftp.name}"]
  #user_data       = "${file("cloud-init/inbox.sh")}"
  network {
    name = "${var.ega_net}"
  }
  block_device {
    uuid                  = "${var.ega_common_snapshot_id}"
    source_type           = "snapshot"
    volume_size           = 10
    destination_type      = "volume"
    boot_index            = 0
    delete_on_termination = true
  }
}
resource "openstack_compute_floatingip_associate_v2" "inbox_fip" {
  floating_ip  = "${openstack_networking_floatingip_v2.inbox_ip.address}"
  instance_id = "${openstack_compute_instance_v2.inbox.id}"
}
resource "openstack_compute_volume_attach_v2" "inbox_attach" {
  instance_id = "${openstack_compute_instance_v2.inbox.id}"
  volume_id   = "${openstack_blockstorage_volume_v2.staging.id}"
}

# ===============================
resource "openstack_compute_instance_v2" "vault" {
  name      = "vault"
  flavor_name = "ssc.small"
  key_pair  = "${openstack_compute_keypair_v2.ega_key.name}"
  security_groups = ["default"]
  #user_data       = "${file("cloud-init/vault.sh")}"
  network {
    name = "${var.ega_net}"
  }
  block_device {
    uuid                  = "${var.ega_common_snapshot_id}"
    source_type           = "snapshot"
    volume_size           = 10
    destination_type      = "volume"
    boot_index            = 0
    delete_on_termination = true
  }
}
resource "openstack_compute_volume_attach_v2" "vault_attach" {
  instance_id = "${openstack_compute_instance_v2.vault.id}"
  volume_id   = "${openstack_blockstorage_volume_v2.vault.id}"
}

# ===============================
resource "openstack_compute_instance_v2" "verify" {
  name      = "verify"
  flavor_name = "ssc.small"
  key_pair  = "${openstack_compute_keypair_v2.ega_key.name}"
  security_groups = ["default"]
  #user_data       = "${file("cloud-init/verify.sh")}"
  network {
    name = "${var.ega_net}"
  }
  block_device {
    uuid                  = "${var.ega_common_snapshot_id}"
    source_type           = "snapshot"
    volume_size           = 10
    destination_type      = "volume"
    boot_index            = 0
    delete_on_termination = true
  }
}

# # ===============================
# resource "openstack_compute_instance_v2" "connectors" {
#   name      = "connectors"
#   flavor_name = "ssc.small"
#   key_pair  = "${openstack_compute_keypair_v2.ega_key.name}"
#   security_groups = ["default"]
#   #user_data       = "${file("cloud-init/connectors.sh")}"
#   network {
#     name = "${var.ega_net}"
#   }
#   block_device {
#     uuid                  = "${var.ega_common_snapshot_id}"
#     source_type           = "snapshot"
#     volume_size           = 10
#     destination_type      = "volume"
#     boot_index            = 0
#     delete_on_termination = true
#   }
# }

# # ===============================
# resource "openstack_compute_instance_v2" "monitors" {
#   name      = "monitors"
#   flavor_name = "ssc.small"
#   key_pair  = "${openstack_compute_keypair_v2.ega_key.name}"
#   security_groups = ["default"]
#   #user_data       = "${file("cloud-init/monitor.sh")}"
#   network {
#     name = "${var.ega_net}"
#   }
#   block_device {
#     uuid                  = "${var.ega_common_snapshot_id}"
#     source_type           = "snapshot"
#     volume_size           = 10
#     destination_type      = "volume"
#     boot_index            = 0
#     delete_on_termination = true
#   }
# }

# ===============================
resource "openstack_compute_instance_v2" "worker" {
  count     = "${var.workers}"
  name      = "${format("worker-%02d", count.index+1)}"
  flavor_name = "ssc.small"
  key_pair  = "${openstack_compute_keypair_v2.ega_key.name}"
  security_groups = ["default"]
  #user_data       = "${file("cloud-init/worker.sh")}"
  network {
    name = "${var.ega_net}"
  }
  block_device {
    uuid                  = "${var.ega_common_snapshot_id}"
    source_type           = "snapshot"
    volume_size           = 10
    destination_type      = "volume"
    boot_index            = 0
    delete_on_termination = true
  }
}

resource "openstack_compute_instance_v2" "keys" {
  name      = "keys"
  flavor_name = "ssc.small"
  key_pair  = "${openstack_compute_keypair_v2.ega_key.name}"
  security_groups = ["default"]
  #user_data       = "${file("cloud-init/keys.sh")}"
  network {
    name = "${var.ega_net}"
  }
  block_device {
    uuid                  = "${var.ega_common_snapshot_id}"
    source_type           = "snapshot"
    volume_size           = 10
    destination_type      = "volume"
    boot_index            = 0
    delete_on_termination = true
  }
}

# ===============================
resource "openstack_compute_instance_v2" "db" {
  name      = "db"
  flavor_name = "ssc.small"
  key_pair  = "${openstack_compute_keypair_v2.ega_key.name}"
  security_groups = ["default","${openstack_compute_secgroup_v2.ega_db.name}"]
  #user_data       = "${file("cloud-init/db.sh")}"
  network {
    name = "${var.ega_net}"
  }
  block_device {
    uuid                  = "${var.ega_db_snapshot_id}"
    source_type           = "snapshot"
    volume_size           = 10
    destination_type      = "volume"
    boot_index            = 0
    delete_on_termination = true
  }
}

# ===============================
resource "openstack_compute_instance_v2" "mq" {
  name      = "mq"
  flavor_name = "ssc.small"
  key_pair  = "${openstack_compute_keypair_v2.ega_key.name}"
  security_groups = ["default","${openstack_compute_secgroup_v2.ega_mq.name}"]
  #user_data       = "${file("cloud-init/mq.sh")}"
  network {
    name = "${var.ega_net}"
  }
  block_device {
    uuid                  = "${var.ega_mq_snapshot_id}"
    source_type           = "snapshot"
    volume_size           = 10
    destination_type      = "volume"
    boot_index            = 0
    delete_on_termination = true
  }
}
