variable ega_key { default = "ega_key" }
variable ega_net {}
variable flavor_name { default = "ssc.xlarge" }
variable flavor_name_keys { default = "ssc.small" }
variable image_name { default = "EGA-common" }

variable count { default = 1 }
variable cidr {}
variable private_ips { type = "list" }
variable private_ip_keys {}
variable lega_conf {}

variable rsa_home {}
variable gpg_home {}
variable gpg_certs {}
variable gpg_passphrase {}

variable certfile { default = "selfsigned.cert" }
variable certkey { default = "selfsigned.key" }


data "archive_file" "rsa" {
  type        = "zip"
  output_path = "${path.module}/rsa_public.zip"

  source {
    content  = "${file("${var.rsa_home}/ega-public.pem")}"
    filename = "ega-public.pem"
  }

  source { # to be removed
    content  = "${file("${var.rsa_home}/ega.pem")}"
    filename = "ega.pem"
  }

}

data "archive_file" "gpg" {
  type        = "zip"
  output_path = "${path.module}/gpg_public.zip"

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
  output_path = "${path.module}/certs_public.zip"

  source {
    content  = "${file("${var.gpg_certs}/${var.certfile}")}"
    filename = "selfsigned.cert"
  }
}

data "template_file" "cloud_init" {
  template = "${file("${path.module}/cloud_init.tpl")}"

  vars {
    boot_script = "${base64encode("${file("${path.module}/boot.sh")}")}"
    lega_script = "${base64encode("${file("${path.module}/lega.sh")}")}"
    hosts = "${base64encode("${file("${path.root}/hosts")}")}"
    conf = "${var.lega_conf}"
    rsa = "${base64encode("${file("${data.archive_file.rsa.output_path}")}")}"
    gpg = "${base64encode("${file("${data.archive_file.gpg.output_path}")}")}"
    certs = "${base64encode("${file("${data.archive_file.certs.output_path}")}")}"
    ega_service_forwarder = "${base64encode("${file("${path.module}/ega-socket-forwarder@.service")}")}"
    ega_service_worker = "${base64encode("${file("${path.module}/ega-worker.service")}")}"
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
    uuid = "${var.ega_net}"
    fixed_ip_v4 = "${var.private_ips[count.index]}"
  }
  user_data       = "${data.template_file.cloud_init.rendered}"
}

################################################################
##             Master GPG-agent
################################################################

data "archive_file" "rsa_private" {
  type        = "zip"
  output_path = "${path.module}/rsa_private.zip"

  source {
    content  = "${file("${var.rsa_home}/ega-public.pem")}"
    filename = "ega-public.pem"
  }

  source {
    content  = "${file("${var.rsa_home}/ega.pem")}"
    filename = "ega.pem"
  }

}

data "archive_file" "gpg_private" {
  type        = "zip"
  output_path = "${path.module}/gpg_private.zip"
  source_dir = "${var.gpg_home}/private-keys-v1.d"
  # Not packaging the openpgp-revocs.d folder
}

data "archive_file" "certs_private" {
  type        = "zip"
  output_path = "${path.module}/certs_private.zip"

  source {
    content  = "${file("${var.gpg_certs}/${var.certfile}")}"
    filename = "selfsigned.cert"
  }

  source {
    content  = "${file("${var.gpg_certs}/${var.certkey}")}"
    filename = "selfsigned.key"
  }
}

data "template_file" "cloud_init_keys" {
  template = "${file("${path.module}/cloud_init_keys.tpl")}"

  vars {
    boot_script = "${base64encode("${file("${path.module}/keys.sh")}")}"
    hosts = "${base64encode("${file("${path.root}/hosts")}")}"
    conf = "${var.lega_conf}"
    gpg_passphrase = "${base64encode("${var.gpg_passphrase}")}"
    rsa = "${base64encode("${file("${data.archive_file.rsa_private.output_path}")}")}"
    certs = "${base64encode("${file("${data.archive_file.certs_private.output_path}")}")}"
    gpg = "${base64encode("${file("${data.archive_file.gpg.output_path}")}")}"
    gpg_private = "${base64encode("${file("${data.archive_file.gpg_private.output_path}")}")}"
    ega_service = "${base64encode("${file("${path.module}/ega-socket-proxy@.service")}")}"
  }
}

resource "openstack_compute_secgroup_v2" "ega_gpg" {
  name        = "ega-gpg"
  description = "GPG socket forwarding"

  rule {
    from_port   = 9010
    to_port     = 9010
    ip_protocol = "tcp"
    cidr        = "${var.cidr}"
  }
}

resource "openstack_compute_instance_v2" "keys" {
  name      = "keys"
  flavor_name = "${var.flavor_name_keys}"
  image_name = "${var.image_name}"
  key_pair  = "${var.ega_key}"
  security_groups = ["default","${openstack_compute_secgroup_v2.ega_gpg.name}"]
  network {
    uuid = "${var.ega_net}"
    fixed_ip_v4 = "${var.private_ip_keys}"
  }
  user_data       = "${data.template_file.cloud_init_keys.rendered}"
}
