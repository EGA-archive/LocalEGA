An NSS module to find the EGA users in a (remote) database

# Compile the library

	make

# Add it to the system

	make install

	echo '/usr/local/lib/ega' > /etc/ld.so.conf.d/ega.conf
	
	ldconfig -v

`ldconfig` recreates the ld cache and also creates some extra links. (important!).

# Make the system use it

Update `/etc/nsswitch.conf` and add the ega module first, for passwd

	passwd: ega files ...
