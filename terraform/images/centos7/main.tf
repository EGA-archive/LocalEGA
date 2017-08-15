variable os_username {}
variable os_password {}
variable pubkey {}

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
  name       = "ega_key"
  public_key = "${var.pubkey}"
}

# ========= Instances =========

resource "openstack_compute_instance_v2" "ega_build_common" {
  name      = "ega-build-common"
  flavor_name = "ssc.small"
  image_name = "CentOS 7 - latest"
  key_pair  = "${openstack_compute_keypair_v2.ega_key.name}"
  security_groups = ["default"]
  network { name = "SNIC 2017/13-34 Internal IPv4 Network" }
  user_data = "${file("${path.module}/common.sh")}"
}

resource "openstack_compute_instance_v2" "ega_build_db" {
  name      = "ega-build-db"
  flavor_name = "ssc.small"
  image_name = "CentOS 7 - latest"
  key_pair  = "${openstack_compute_keypair_v2.ega_key.name}"
  security_groups = ["default"]
  network { name = "SNIC 2017/13-34 Internal IPv4 Network" }
  user_data = "${file("${path.module}/db.sh")}"
}

resource "openstack_compute_instance_v2" "ega_build_mq" {
  name      = "ega-build-mq"
  flavor_name = "ssc.small"
  image_name = "CentOS 7 - latest"
  key_pair  = "${openstack_compute_keypair_v2.ega_key.name}"
  security_groups = ["default"]
  network { name = "SNIC 2017/13-34 Internal IPv4 Network" }
  user_data = "${file("${path.module}/mq.sh")}"
}
