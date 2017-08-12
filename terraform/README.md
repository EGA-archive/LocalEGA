# Deploy LocalEGA on Openstack using Terraform

You need to create a `main.auto.tfvars` file (in that same folder) with the following information:

```
pubkey = "<path/to/your/public/key>"
os_username = "<your-openstack-keystone-username>"
os_password = "<your-openstack-keystone-password>"
db_password = "<your-secret-password>"

gpg_home  = "<path/to/gpg/folder>"
gpg_certs = "<path/to/certs/folder>"  # including .cert and .key files
rsa_home  = "<path/to/rsa/folder>"    # including ega-public.pem and ega.pem files
gpg_passphrase = "<something-complex>"
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

