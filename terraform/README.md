# Deploy LocalEGA on Openstack using Terraform

You need to create a `vars/ega.tfvars` file with the following information:

```
pubkey = "ssh-rsa AAAABBBBB..... blabla....your ssh public key"
os_username = "<your-openstack-keystone-username>"
os_password = "<your-openstack-keystone-password>"
db_password = "<your-secret-password>"
```

You must then initialize Terraform and, optionally, you can check what's to be done with:

	terraform init -var-file=vars/ega.tfvars
	terraform plan -var-file=vars/ega.tfvars

## Running

	# Create network first
	terraform apply -var-file=vars/ega.tfvars -target=openstack_networking_router_interface_v2.ega_router_interface
	
	# ...and cue music
	terraform apply -var-file=vars/ega.tfvars
	
## Stopping

	terraform destroy

## Build the EGA-common, EGA-db and EGA-mq images

	terraform apply -var-file=vars/ega.tfvars images/centos7

