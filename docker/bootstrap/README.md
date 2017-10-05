The following is not technically part of LocalEGA but it can useful to
get started on it.

We have created 2 bash scripts, one for the generation of the GnuPG
key, RSA master key pair, SSL certificates for internal communication,
passwords, default users, etc...

Use `-h` to see the possible options of each script.

We create a separate folder and generate all the necessary files in it.

	./generate.sh
	
We then move the .env and .env.d into place (backing them up in the
destination location if there was already a version)

	./populate.sh
	
The passwords are in `private/.trace` (if you did not use
`--private_dir`)

If you don't have the required tools installed on your machine (namely
GnuPG 2.2.1 and OpenSSL 1.0.2), you can use the `nbis/ega:worker`
image that is already setup:

	# In that current folder
	docker run --rm -it -v ${PWD}:/ega nbis/ega:worker /ega/generate.sh -f
	# That creates a folder, named 'private', with all the settings
	# Call populate.sh afterwards
	

Alternatively, albeit not recommended, you
can [generate the private data yourself](info.md), and adapt the
different PATHs in the `.env` and `.env.d` settings.

