# Deploy LocalEGA on Openstack using Terraform

You need to create a `main.auto.tfvars` file (in that same folder) with the following information:

```
pubkey = "ssh-rsa AAAABBBBB..... blabla....your ssh public key"
os_username = "<your-openstack-keystone-username>"
os_password = "<your-openstack-keystone-password>"
db_password = "<your-secret-password>"
```

You must then initialize Terraform and, optionally, you can check what's to be done with:

	terraform init
	terraform plan

## Running

	# Create network first
	terraform apply -target=openstack_networking_router_interface_v2.ega_router_interface
	
	# ...and cue music
	terraform apply
	
## Stopping

	terraform destroy

## Build the EGA-common, EGA-db and EGA-mq images

	terraform apply images/centos7

