# Makefile for the NSS module used in Local EGA

SOURCES = interface.c config.c backend.c
OBJECTS = $(SOURCES:.c=.o)

LIBS=-lpthread -lpq

all: libnss_ega.so.2

.SUFFIXES: .c .o .so

libnss_ega.so.2: nss-ega.h $(OBJECTS)
	gcc -shared -o $@ -Wl,-soname,$@ $(LIBS) $(OBJECTS)
#	gcc -g -O2 -o $@ -rpath /usr/local/lib -module -version-info 2 -lpq $(OBJECTS)

clean:
	-rm -f libnss_ega.so.2 $(OBJECTS)

%.o: %.c
	@echo "Compiling $<"
	gcc -I. -g -O2 -fPIC -c $<

install: libnss_ega.so.2
	@echo 'Installing'
	cp $< /usr/local/lib/$<
	[ -L /usr/local/lib/libnss_ega.so ] && unlink /usr/local/lib/libnss_ega.so
	cd /usr/local/lib/ && ln -s $< libnss_ega.so
	cp nss-ega.conf /usr/local/etc/nss-ega.conf
