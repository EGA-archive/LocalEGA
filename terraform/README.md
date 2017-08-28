# Deploy LocalEGA on Openstack using Terraform

You need to create a `main.auto.tfvars` file (in that same folder) with the following information:

```
pubkey      = "ssh-rsa AAAABBBBBB ... bla bla....your-public-key"
os_username = "<your-openstack-keystone-username>"
os_password = "<your-openstack-keystone-password>"
db_password = "<your-secret-password>"

gpg_home  = "<path/to/gpg/folder>"
gpg_certs = "<path/to/certs/folder>"  # including .cert and .key files
rsa_home  = "<path/to/rsa/folder>"    # including ega-public.pem and ega.pem files
gpg_passphrase = "<something-complex>"

lega_conf = "<path/to/your/ini/file>"
```

You must then initialize Terraform:

	terraform init
	terraform plan # to see what's to be done (optional)
	
	# it helps to create the network components first
	terraform apply -target=module.network

## Running

	# ...and cue music
	terraform apply
	
## Stopping

	terraform destroy

## Build the EGA-common, EGA-db and EGA-mq images

	terraform apply images/centos7

