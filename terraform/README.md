# Deploy LocalEGA on Openstack using Terraform

You need to create a `main.auto.tfvars` file (in that same folder) with the following information:

	os_username = "<your-openstack-keystone-username>"
	os_password = "<your-openstack-keystone-password>"
	pubkey      = "ssh-rsa AAAABBBBBB ... bla bla....your-public-key"
	
	lega_conf   = "<path/to/your/ini/file>"
	db_password = "<your-secret-password>"

	gpg_home    = "<path/to/gpg/folder>"
	gpg_certs   = "<path/to/certs/folder>"  # including .cert and .key files
	rsa_home    = "<path/to/rsa/folder>"    # including ega-public.pem and ega.pem files
	gpg_passphrase = "<something-complex>"

## Initialize Terraform

	terraform init
	
	# Check what's to be done (optional)
	terraform plan
	
## Running

	terraform apply
	
That's it.	

----
If it fails, it might be a good idea to bring them up little at a time.

So... network first:

	terraform apply -target=module.network

...database, Message Borker and Logger:

	terraform apply -target=module.db -target=module.mq -target=module.monitors

...connecting to CentralEGA:

	terraform apply -target=module.connectors

...and the rest:

	terraform apply

## Stopping

	terraform destroy

Type `yes` for confirmation (or use the `--force` flag)

## Build the EGA-common, EGA-db and EGA-mq images

	terraform apply images/centos7
