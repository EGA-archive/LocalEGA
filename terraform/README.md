# Deploy LocalEGA on Openstack using Terraform

You need to create a `variables.tf` file with the following information:

```
variable "pubkey" {
  description = "The Key Pair to boot machine"
  default     = "ssh-rsa AAAABBBBB..... blabla....your ssh public key"
}

variable "os_username" {
  default = "<your-openstack-keystone-username>"
}
variable "os_password" {
  default = "<your-openstack-keystone-password>"
}

variable "workers" {
  default = <number-of-workers>
}

variable "ega_net" {
  default = "<name-of-the-neutron-network>"
}

variable "ega_common_snapshot_id" {
  default = "<id-of-the-image-for-the-common-instances>"
}
variable "ega_mq_snapshot_id" {
  default = "<id-of-the-image-for-the-message-broker-instance>"
}
variable "ega_db_snapshot_id" {
  default = "<id-of-the-image-for-the-database-instance>"
}
```

## Running

	terraform plan  # check what's to be done
	terraform apply # ...cue music
	

## Stopping

	terraform destroy

