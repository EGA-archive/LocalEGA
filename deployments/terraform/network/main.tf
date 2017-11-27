variable cidr {}

resource "openstack_networking_network_v2" "ega_net" {
  name           = "ega_net"
  admin_state_up = "true"
}

resource "openstack_networking_subnet_v2" "ega_subnet" {
  network_id  = "${openstack_networking_network_v2.ega_net.id}"
  name        = "ega_subnet"
  cidr        = "${var.cidr}"
  enable_dhcp = true
  ip_version  = 4
  dns_nameservers = ["130.239.1.90","8.8.8.8"]
}

resource "openstack_networking_router_interface_v2" "ega_router_interface" {
  router_id = "1f852a3d-f7ea-45ae-9cba-3160c2029ba1"
  subnet_id = "${openstack_networking_subnet_v2.ega_subnet.id}"
}

output "net_id" {
  value = "${openstack_networking_network_v2.ega_net.id}"
}
