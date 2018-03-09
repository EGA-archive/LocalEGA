variable ega_key { default = "ega_key" }
variable ega_net {}
variable flavor_name_compute {}
variable flavor_name {}
variable image_name { default = "EGA-common" }

variable count { default = 1 }
variable cidr {}
variable private_ips { type = "list" }
variable private_ip_keys {}

variable instance_data {}

data "template_file" "cloud_init" {
  template = "${file("${path.module}/cloud_init.tpl")}"

  vars {
    hosts       = "${base64encode("${file("${path.root}/hosts")}")}"
    hosts_allow = "${base64encode("${file("${path.root}/hosts.allow")}")}"
    lega_conf   = "${base64encode("${file("${var.instance_data}/ega.conf")}")}"
    ega_options = "${base64encode("${file("${path.root}/systemd/options")}")}"
    ega_slice   = "${base64encode("${file("${path.root}/systemd/ega.slice")}")}"
    ega_ingest  = "${base64encode("${file("${path.root}/systemd/ega-ingestion@.service")}")}"
    ega_inbox_mount   = "${base64encode("${file("${path.root}/systemd/ega-inbox.mount")}")}"
    ega_staging_mount = "${base64encode("${file("${path.root}/systemd/ega-staging.mount")}")}"
  }
}

resource "openstack_compute_instance_v2" "worker" {
  count     = "${var.count}"
  name      = "${format("worker-%02d", count.index+1)}"
  flavor_name = "${var.flavor_name_compute}"
  image_name = "${var.image_name}"
  key_pair  = "${var.ega_key}"
  security_groups = ["default"]
  network {
    uuid = "${var.ega_net}"
    fixed_ip_v4 = "${var.private_ips[count.index]}"
  }
  user_data = "${data.template_file.cloud_init.rendered}"
}

################################################################
##             Key Server
################################################################

data "template_file" "cloud_init_keys" {
  template = "${file("${path.module}/cloud_init_keys.tpl")}"

  vars {
    iptables          = "${base64encode("${file("${path.module}/iptables")}")}"
    hosts             = "${base64encode("${file("${path.root}/hosts")}")}"
    hosts_allow       = "${base64encode("${file("${path.root}/hosts.allow")}")}"
    lega_conf         = "${base64encode("${file("${var.instance_data}/ega.conf")}")}"
    keys_conf         = "${base64encode("${file("${var.instance_data}/keys.conf")}")}"
    ssl_cert          = "${base64encode("${file("${var.instance_data}/certs/ssl.cert")}")}"
    ssl_key           = "${base64encode("${file("${var.instance_data}/certs/ssl.key")}")}"
    rsa_pub           = "${base64encode("${file("${var.instance_data}/rsa/ega.pub")}")}"
    rsa_sec           = "${base64encode("${file("${var.instance_data}/rsa/ega.sec")}")}"
    pgp_pub           = "${base64encode("${file("${var.instance_data}/pgp/ega.pub")}")}"
    pgp_sec           = "${base64encode("${file("${var.instance_data}/pgp/ega.sec")}")}"
    ega_options       = "${base64encode("${file("${path.root}/systemd/options")}")}"
    ega_slice         = "${base64encode("${file("${path.root}/systemd/ega.slice")}")}"
    ega_keys          = "${base64encode("${file("${path.root}/systemd/ega-keyserver.service")}")}"
  }
}

resource "openstack_compute_secgroup_v2" "ega_keys" {
  name        = "ega-keys"
  description = "GPG socket forwarding and Keys Server"

  rule {
    from_port   = 443
    to_port     = 443
    ip_protocol = "tcp"
    cidr        = "${var.cidr}"
  }
}

resource "openstack_compute_instance_v2" "keys" {
  name        = "keys"
  flavor_name = "${var.flavor_name}"
  image_name  = "${var.image_name}"
  key_pair    = "${var.ega_key}"
  security_groups = ["default","${openstack_compute_secgroup_v2.ega_keys.name}"]
  network {
    uuid = "${var.ega_net}"
    fixed_ip_v4 = "${var.private_ip_keys}"
  }
  user_data = "${data.template_file.cloud_init_keys.rendered}"
}
