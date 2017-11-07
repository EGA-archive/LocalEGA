The following is not technically part of LocalEGA but it can useful to
get started on it.

We have created 2 bash scripts, one for the generation of the GnuPG
key, RSA master key pair, SSL certificates for internal communication,
passwords, default users, etc...

Use `-h` to see the possible options of each script.

We create a separate folder and generate all the necessary files in it (require
GnuPG 2.2.1, OpenSSL 1.0.2 and Python 3.6.1). Note that potential error
messages can be found at the file `.err` in the same folder.

	./cega.sh
	./generate.sh -- <LocalEGA-instance>
	
We then move the `.env` and `.env.d/` into place (backing them up in the
destination location if there was already a version)

	./populate.sh
	
The passwords are in `private/.trace.*` (if you did not use `--private_dir`)

If you don't have the required tools installed on your machine (namely
GnuPG 2.2.1, OpenSSL 1.0.2 and Python 3.6.1), you can use the `nbis/ega:worker`
image that you have built up with the `make` command in the [images](../images) folder:

In the same folder as `generate.sh`, run

	docker run --rm -it -v ${PWD}:/ega nbis/ega:worker /ega/generate.sh -f -- swe1

That will create a folder, named 'private', with all the settings
After that, you can run `./populate.sh` to move the `.env` and `.env.d/` into
their destination
	

Alternatively, albeit not recommended, you
can [generate the private data yourself](info.md), and adapt the
different PATHs in the `.env` and `.env.d` settings.


## Troubleshooting

* If the commands `./cega.sh` and `./generate.sh` take more than a
  few seconds to run, it is usually because your computer does not
  have enough entropy. You can use the program `rng-tools` to solve
  this problem. E.g. on Debian/Ubuntu system, install the software by

	   sudo apt-get install rng-tools

  and then run

 	  sudo rngd -r /dev/urandom


