variable ega_key { default = "ega_key" }
variable ega_net {}
variable flavor_name {}
variable image_name { default = "EGA-common" }

variable volume_size { default = 100 }

variable private_ip {}
variable instance_data {}
variable cidr {}
variable pool {}

resource "openstack_compute_secgroup_v2" "ega_inbox" {
  name        = "ega-inbox"
  description = "SFTP inbox rules"

  rule {
    from_port   = 22
    to_port     = 22
    ip_protocol = "tcp"
    cidr        = "0.0.0.0/0"
  }
}

data "template_file" "cloud_init" {
  template = "${file("${path.module}/cloud_init.tpl")}"

  vars {
    cidr        = "${var.cidr}"
    conf        = "${base64encode("${file("${var.instance_data}/ega.conf")}")}"
    auth_conf   = "${base64encode("${file("${var.instance_data}/auth.conf")}")}"
    hosts       = "${base64encode("${file("${path.root}/hosts")}")}"
    hosts_allow = "${base64encode("${file("${path.root}/hosts.allow")}")}"
    sshd_config = "${base64encode("${file("${path.module}/sshd_config")}")}"
    sshd_pam    = "${base64encode("${file("${path.module}/pam.sshd")}")}"
    ega_pam     = "${base64encode("${file("${path.module}/pam.ega")}")}"
    fuse_cleanup= "${base64encode("${file("${path.module}/fuse_cleanup.sh")}")}"
    ega_ssh_keys= "${base64encode("${file("${var.instance_data}/ega_ssh_keys.sh")}")}"
    ega_mount   = "${base64encode("${file("${path.root}/systemd/ega.mount")}")}"
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

# ===== Floating IP =====
resource "openstack_networking_floatingip_v2" "fip" {
  pool = "${var.pool}"
}
resource "openstack_compute_floatingip_associate_v2" "inbox_fip" {
  floating_ip  = "${openstack_networking_floatingip_v2.fip.address}"
  instance_id = "${openstack_compute_instance_v2.inbox.id}"
}

output "address" {
  value = "${openstack_networking_floatingip_v2.fip.address}"
}
