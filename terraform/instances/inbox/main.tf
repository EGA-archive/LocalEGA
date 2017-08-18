variable ega_key { default = "ega_key" }
variable ega_net {}
variable flavor_name { default = "ssc.small" }
variable image_name { default = "EGA-common" }

variable volume_size { default = 100 }

variable private_ip {}
variable lega_conf {}
variable cidr {}

data "template_file" "cloud_init" {
  template = "${file("${path.module}/cloud_init.tpl")}"

  vars {
    boot_script = "${base64encode("${file("${path.module}/boot.sh")}")}"
    lega_script = "${base64encode("${file("${path.module}/lega.sh")}")}"
    hosts = "${base64encode("${file("${path.root}/hosts")}")}"
    conf = "${var.lega_conf}"
    cidr = "${var.cidr}"
  }
}

resource "openstack_compute_secgroup_v2" "ega_inbox" {
  name        = "ega-inbox"
  description = "Inbox access"

  rule {
    from_port   = 22
    to_port     = 22
    ip_protocol = "tcp"
    cidr        = "0.0.0.0/0"
  }
  rule {
    from_port   = 21
    to_port     = 21
    ip_protocol = "tcp"
    cidr        = "0.0.0.0/0"
  }
  rule {
    from_port   = 6000
    to_port     = 6000
    ip_protocol = "tcp"
    cidr        = "0.0.0.0/0"
  }
  rule {
    from_port   = 6001
    to_port     = 6001
    ip_protocol = "tcp"
    cidr        = "0.0.0.0/0"
  }
}

resource "openstack_compute_instance_v2" "inbox" {
  name      = "inbox"
  flavor_name = "${var.flavor_name}"
  image_name = "${var.image_name}"
  key_pair  = "${var.ega_key}"
  security_groups = ["default","${openstack_compute_secgroup_v2.ega_inbox.name}"]
  network {
    uuid = "${var.ega_net}"
    fixed_ip_v4 = "${var.private_ip}"
  }
  user_data       = "${data.template_file.cloud_init.rendered}"
}

# ===== Floating IP =====
resource "openstack_networking_floatingip_v2" "inbox_ip" {
  pool = "Public External IPv4 Network"
}
resource "openstack_compute_floatingip_associate_v2" "inbox_fip" {
  floating_ip  = "${openstack_networking_floatingip_v2.inbox_ip.address}"
  instance_id = "${openstack_compute_instance_v2.inbox.id}"
}

# ===== Staging area / Inbox volume =====
resource "openstack_blockstorage_volume_v2" "disk" {
  name = "inbox"
  description = "Inbox and Staging area"
  size = "${var.volume_size}"
}
resource "openstack_compute_volume_attach_v2" "inbox_attach" {
  instance_id = "${openstack_compute_instance_v2.inbox.id}"
  volume_id   = "${openstack_blockstorage_volume_v2.disk.id}"
  device = "/dev/vdb" # might cause re-attaching upon each 'apply'
}
