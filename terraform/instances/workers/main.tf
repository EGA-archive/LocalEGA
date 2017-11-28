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
    boot_script = "${base64encode("${file("${path.module}/boot.sh")}")}"
    hosts       = "${base64encode("${file("${path.root}/hosts")}")}"
    hosts_allow = "${base64encode("${file("${path.root}/hosts.allow")}")}"
    lega_conf   = "${base64encode("${file("${var.instance_data}/ega.conf")}")}"
    ssl_cert    = "${base64encode("${file("${var.instance_data}/certs/ssl.cert")}")}"
    gpg_pubring = "${base64encode("${file("${var.instance_data}/gpg/pubring.kbx")}")}"
    gpg_trustdb = "${base64encode("${file("${var.instance_data}/gpg/trustdb.gpg")}")}"
    ega_options = "${base64encode("${file("${path.root}/systemd/options")}")}"
    ega_slice   = "${base64encode("${file("${path.root}/systemd/ega.slice")}")}"
    ega_socket  = "${base64encode("${file("${path.root}/systemd/ega-socket-forwarder.socket")}")}"
    ega_forward = "${base64encode("${file("${path.root}/systemd/ega-socket-forwarder.service")}")}"
    ega_ingest  = "${base64encode("${file("${path.root}/systemd/ega-ingestion.service")}")}"
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
##             Master GPG-agent
################################################################

# data "archive_file" "gpg_private" {
#   type        = "zip"
#   output_path = "${var.instance_data}/gpg_private.zip"
#   source_dir = "${var.instance_data}/gpg/private-keys-v1.d"
#   # Not packaging the openpgp-revocs.d folder
# }

# data "template_file" "cloud_init_keys" {
#   template = "${file("${path.module}/cloud_init_keys.tpl")}"

#   vars {
#     boot_script = "${base64encode("${file("${path.module}/keys.sh")}")}"
#     preset_script="${base64encode("${file("${var.instance_data}/preset.sh")}")}"
#     hosts       = "${base64encode("${file("${path.root}/hosts")}")}"
#     hosts_allow = "${base64encode("${file("${path.root}/hosts.allow")}")}"
#     lega_conf   = "${base64encode("${file("${var.instance_data}/ega.conf")}")}"
#     keys_conf   = "${base64encode("${file("${var.instance_data}/keys.conf")}")}"
#     ssl_cert    = "${base64encode("${file("${var.instance_data}/certs/ssl.cert")}")}"
#     ssl_key     = "${base64encode("${file("${var.instance_data}/certs/ssl.key")}")}"
#     rsa_pub     = "${base64encode("${file("${var.instance_data}/rsa/ega.pub")}")}"
#     rsa_sec     = "${base64encode("${file("${var.instance_data}/rsa/ega.sec")}")}"
#     gpg_agent   = "${base64encode("${file("${path.module}/gpg-agent.conf")}")}"
#     gpg_pubring = "${base64encode("${file("${var.instance_data}/gpg/pubring.kbx")}")}"
#     gpg_trustdb = "${base64encode("${file("${var.instance_data}/gpg/trustdb.gpg")}")}"
#     gpg_private = "${base64encode("${file("${data.archive_file.gpg_private.output_path}")}")}"
#     ega_options = "${base64encode("${file("${path.root}/systemd/options")}")}"
#     ega_slice   = "${base64encode("${file("${path.root}/systemd/ega.slice")}")}"
#     ega_socket  = "${base64encode("${file("${path.root}/systemd/ega-socket-forwarder.socket")}")}"
#     ega_proxy   = "${base64encode("${file("${path.root}/systemd/ega-socket-proxy.service")}")}"
#     ega_keys    = "${base64encode("${file("${path.root}/systemd/ega-keys.service")}")}"
#   }
# }

# resource "openstack_compute_secgroup_v2" "ega_gpg" {
#   name        = "ega-gpg"
#   description = "GPG socket forwarding"

#   rule {
#     from_port   = 9010
#     to_port     = 9010
#     ip_protocol = "tcp"
#     cidr        = "${var.cidr}"
#   }
# }

# resource "openstack_compute_instance_v2" "keys" {
#   name      = "keys"
#   flavor_name = "${var.flavor_name}"
#   image_name = "${var.image_name}"
#   key_pair  = "${var.ega_key}"
#   security_groups = ["default","${openstack_compute_secgroup_v2.ega_gpg.name}"]
#   network {
#     uuid = "${var.ega_net}"
#     fixed_ip_v4 = "${var.private_ip_keys}"
#   }
#   user_data = "${data.template_file.cloud_init_keys.rendered}"
# }
