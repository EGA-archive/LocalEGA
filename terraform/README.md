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

Of course, it is necessary to create your own `lega.conf`, with your EGA settings (and place it in that same folder).

## Running

	# Create network first
	terraform apply -target=module.network
	
	# ...and cue music
	terraform apply
	
## Stopping

	terraform destroy

## Build the EGA-common, EGA-db and EGA-mq images

	terraform apply images/centos7

