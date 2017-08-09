variable ega_key { default = "ega_key" }
variable ega_net { default = "SNIC 2017/13-34 Internal IPv4 Network" }
variable flavor_name { default = "ssc.small" }
variable image_name { default = "EGA-common" }

resource "openstack_compute_secgroup_v2" "ega_web" {
  name        = "ega-web"
  description = "Web access"

  rule {
    from_port   = 80
    to_port     = 80
    ip_protocol = "tcp"
    cidr        = "0.0.0.0/0"
  }
  rule {
    from_port   = 443
    to_port     = 443
    ip_protocol = "tcp"
    cidr        = "0.0.0.0/0"
  }
}

resource "openstack_compute_instance_v2" "frontend" {
  name      = "frontend"
  flavor_name = "${var.flavor_name}"
  image_name = "${var.image_name}"
  key_pair  = "${var.ega_key}"
  security_groups = ["default","${openstack_compute_secgroup_v2.ega_web.name}"]
  #user_data       = "${file("${path.module}/boot.sh")}"
  network { name = "${var.ega_net}" }
}

resource "openstack_networking_floatingip_v2" "frontend_ip" {
  pool = "Public External IPv4 Network"
}
resource "openstack_compute_floatingip_associate_v2" "frontend_fip" {
  floating_ip  = "${openstack_networking_floatingip_v2.frontend_ip.address}"
  instance_id = "${openstack_compute_instance_v2.frontend.id}"
}
