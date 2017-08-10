resource "openstack_compute_secgroup_v2" "ega_test" {
  name        = "ega-test"
  description = "Test rules"

  rule {
    from_port   = 5432
    to_port     = 5432
    ip_protocol = "tcp"
    cidr        = "0.0.0.0/0"
  }
}

resource "openstack_compute_instance_v2" "test" {
  name      = "test"
  flavor_name = "ssc.small"
  image_name = "EGA-common"
  key_pair  = "ega_key"
  security_groups = ["default"]
  network { name = "SNIC 2017/13-34 Internal IPv4 Network" }
}

resource "openstack_compute_instance_v2" "test_db" {
  name      = "db-build"
  flavor_name = "ssc.small"
  image_name = "CentOS 7 - latest"
  key_pair  = "ega_key"
  security_groups = ["default","${openstack_compute_secgroup_v2.ega_test.name}"]
  network { name = "SNIC 2017/13-34 Internal IPv4 Network" }
  #user_data = "${file("${path.module}/../db/cloud_init")}"
}

# ======== Floating IP ===========
resource "openstack_networking_floatingip_v2" "test_ip" {
  pool = "Public External IPv4 Network"
}
resource "openstack_compute_floatingip_associate_v2" "test_fip" {
  floating_ip  = "${openstack_networking_floatingip_v2.test_ip.address}"
  instance_id = "${openstack_compute_instance_v2.test_db.id}"
}
