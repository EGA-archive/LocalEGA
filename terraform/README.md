# Deploy LocalEGA on Openstack using Terraform

You need to create a `vars/ega.tfvars` file with the following information:

```
pubkey = "ssh-rsa AAAABBBBB..... blabla....your ssh public key"
os_username = "<your-openstack-keystone-username>"
os_password = "<your-openstack-keystone-password>"
db_password = "<your-secret-password>"
```

## Running

	terraform init -var-file=vars/ega.tfvars
	terraform plan -var-file=vars/ega.tfvars  # check what's to be done
	terraform apply -var-file=vars/ega.tfvars # ...cue music
	
## Stopping

	terraform destroy

## Build the EGA-common, EGA-db and EGA-mq images

	terraform apply -var-file=vars/ega.tfvars images/centos7

