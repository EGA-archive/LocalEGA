# Deploy LocalEGA on Openstack using Terraform

You need to create a `variables.tf` file with the following information:

```
variable "pubkey" {
  default     = "ssh-rsa AAAABBBBB..... blabla....your ssh public key"
}

variable "os_username" {
  default = "<your-openstack-keystone-username>"
}

variable "os_password" {
  default = "<your-openstack-keystone-password>"
}

variable "ega_net" {
  default = "<name-of-the-neutron-network>"
}

```

## Running

	terraform plan  # check what's to be done
	terraform apply # ...cue music
	

## Stopping

	terraform destroy

