variable ega_key { default = "ega_key" }
variable ega_net {}
variable flavor_name { default = "ssc.small" }
variable image_name { default = "EGA-mq" }

variable private_ip {}

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

data "template_file" "cloud_init" {
  template = "${file("${path.module}/cloud_init.tpl")}"

  vars {
    rabbitmq_config = "${base64encode("${file("${path.root}/../docker/images/mq/rabbitmq.config")}")}"
    rabbitmq_defs = "${base64encode("${file("${path.root}/../docker/images/mq/rabbitmq.json")}")}"
  }
}

resource "openstack_compute_instance_v2" "mq" {
  name      = "mq"
  flavor_name = "${var.flavor_name}"
  image_name = "${var.image_name}"
  key_pair  = "${var.ega_key}"
  security_groups = ["default","${openstack_compute_secgroup_v2.ega_mq.name}"]
  network {
    uuid = "${var.ega_net}"
    fixed_ip_v4 = "${var.private_ip}"
  }
  user_data = "${data.template_file.cloud_init.rendered}"
}
