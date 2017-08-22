# Makefile for the NSS module used in Local EGA

SOURCES = interface.c config.c backend.c
OBJECTS = $(SOURCES:.c=.o)

all: libnss_ega.so.2

.SUFFIXES: .c .o .so

libnss_ega.so.2: nss-ega.h $(OBJECTS)
	gcc -shared -o $@ -Wl,-soname,$@ -lpq $(OBJECTS)
#	gcc -g -O2 -o $@ -rpath /usr/local/lib -module -version-info 2 -lpq $(OBJECTS)

clean:
	-rm -f libnss_ega.so $(OBJECTS)

%.o: %.c
	@echo "Compiling $<"
	gcc -I. -g -O2 -c -lpq $<

install: libnss_ega.so.2
	@echo 'Installing'
	cp $< /usr/local/lib/$<
	cp nss-ega.conf /usr/local/etc/nss-ega.conf


