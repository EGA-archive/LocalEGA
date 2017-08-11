variable ega_key { default = "ega_key" }
variable flavor_name { default = "ssc.xlarge" }
variable flavor_name_keys { default = "ssc.small" }
variable image_name { default = "EGA-common" }

variable count { default = 1 }
variable private_ips { type = "list" }
variable private_ip_keys {}

variable rsa_home {}
variable gpg_home {}
variable certs {}

data "archive_file" "rsa" {
  type        = "zip"
  source_dir = "${var.rsa_home}"
  output_path = "${path.module}/build/rsa.zip"
}

data "archive_file" "gpg" {
  type        = "zip"
  output_path = "${path.module}/build/gpg.zip"
  source {
    content  = "${file("${var.gpg_home}/pubring.kbx")}"
    filename = "pubring.kbx"
  }
  source {
    content  = "${file("${var.gpg_home}/trustdb.gpg")}"
    filename = "trustdb.gpg"
  }
}

data "archive_file" "certs" {
  type        = "zip"
  output_path = "${path.module}/build/certs.zip"
  source {
    content  = "${file("${var.certs}/cert.pem")}"
    filename = "ega.cert"
  }
}

data "template_file" "cloud_init" {
  template = "${file("${path.module}/cloud_init.tpl")}"

  vars {
    boot_script = "${base64encode("${file("${path.module}/boot.sh")}")}"
    hosts = "${base64encode("${file("${path.root}/hosts")}")}"
    conf = "${base64encode("${file("${path.root}/lega.conf")}")}"
    rsa = "${file("${data.archive_file.rsa.output_path}")}"
    gpg = "${file("${data.archive_file.gpg.output_path}")}"
    certs = "${file("${data.archive_file.certs.output_path}")}"
  }
}

resource "openstack_compute_instance_v2" "worker" {
  count     = "${var.count}"
  name      = "${format("worker-%02d", count.index+1)}"
  flavor_name = "${var.flavor_name}"
  image_name = "${var.image_name}"
  key_pair  = "${var.ega_key}"
  security_groups = ["default"]
  network {
    name = "ega_net"
    fixed_ip_v4 = "${var.private_ips[count.index]}"
  }
  user_data       = "${data.template_file.cloud_init.rendered}"
}

################################################################
##             Master GPG-agent
################################################################

data "archive_file" "rsa_keys" {
  type        = "zip"
  source_dir = "${var.rsa_home}"
  output_path = "${path.module}/build/rsa_keys.zip"
}

data "archive_file" "gpg_keys" {
  type        = "zip"
  output_path = "${path.module}/build/gpg_keys.zip"
  source {
    content  = "${file("${var.gpg_home}/pubring.kbx")}"
    filename = "pubring.kbx"
  }
  source {
    content  = "${file("${var.gpg_home}/trustdb.gpg")}"
    filename = "trustdb.gpg"
  }
  # source_dir = "${var.gpg_home}/openpgp-revocs.d"
  # source_dir = "${var.gpg_home}/private-keys-v1.d"
}

data "archive_file" "certs_keys" {
  type        = "zip"
  output_path = "${path.module}/build/certs_keys.zip"
  source {
    content  = "${file("${var.certs}/cert.pem")}"
    filename = "ega.cert"
  }
  source {
    content  = "${file("${var.certs}/key.pem")}"
    filename = "ega.key"
  }
}

data "template_file" "cloud_init_keys" {
  template = "${file("${path.module}/cloud_init_keys.tpl")}"

  vars {
    boot_script = "${base64encode("${file("${path.module}/keys.sh")}")}"
    hosts = "${base64encode("${file("${path.root}/hosts")}")}"
    conf = "${base64encode("${file("${path.root}/lega.conf")}")}"
    rsa = "${file("${data.archive_file.rsa_keys.output_path}")}"
    gpg = "${file("${data.archive_file.gpg_keys.output_path}")}"
    certs = "${file("${data.archive_file.certs_keys.output_path}")}"
  }
}

resource "openstack_compute_secgroup_v2" "ega_gpg" {
  name        = "ega-gpg"
  description = "GPG socket forwarding"

  rule {
    from_port   = 9010
    to_port     = 9010
    ip_protocol = "tcp"
    cidr        = "0.0.0.0/0"
  }
}

resource "openstack_compute_instance_v2" "keys" {
  name      = "keys"
  flavor_name = "${var.flavor_name_keys}"
  image_name = "${var.image_name}"
  key_pair  = "${var.ega_key}"
  security_groups = ["default","${openstack_compute_secgroup_v2.ega_gpg.name}"]
  network {
    name = "ega_net"
    fixed_ip_v4 = "${var.private_ip_keys}"
  }
  user_data       = "${data.template_file.cloud_init_keys.rendered}"
}
