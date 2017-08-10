variable ega_key { default = "ega_key" }
variable ega_net { default = "SNIC 2017/13-34 Internal IPv4 Network" }
variable flavor_name { default = "ssc.small" }
variable image_name { default = "EGA-mq" }

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

resource "openstack_compute_instance_v2" "mq" {
  name      = "mq"
  flavor_name = "${var.flavor_name}"
  image_name = "${var.image_name}"
  key_pair  = "${var.ega_key}"
  security_groups = ["default","${openstack_compute_secgroup_v2.ega_mq.name}"]
  network { name = "${var.ega_net}" }
}

output "private_ip" {
  value = "${openstack_compute_instance_v2.mq.network.0.fixed_ip_v4}"
}
