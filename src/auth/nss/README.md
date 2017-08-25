An NSS module to find the EGA users in a (remote) database

# Compile the library

	make

# Add the library to the system:

	make install
	cat > /etc/ld.so.conf.d/ega.conf <<EOF
	/usr/local/lib/ega
	EOF
	ldconfig -v

`ldconfig` recreates the ld cache and also create some extra links.

# Make the system use it

Update /etc/nsswitch.conf and add the ega module first, for passwd

passwd: ega files ...
