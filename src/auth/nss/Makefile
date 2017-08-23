# Makefile for the NSS module used in Local EGA

LD_SONAME=-Wl,-soname,libnss_ega.so.2
LIBRARY=libnss_ega.so.2.0
LINKS=libnss_ega.so.2 libnss_ega.so

CC=gcc
CFLAGS=-Wall -Wstrict-prototypes -Werror -fPIC -O2 -I.
LIBS=-lpthread -lpq

LIBDIR=/usr/local/lib

SOURCES = interface.c config.c backend.c
OBJECTS = $(SOURCES:%.c=%.o)

.PHONY: clean install
.SUFFIXES: .c .o .so .so.2 .so.2.0

all: $(LIBRARY)

debug: CFLAGS += -DDEBUG -DDEBUG_SYSLOG -g
debug: $(LIBRARY)

$(LIBRARY): nss-ega.h $(OBJECTS)
	$(CC) -shared $(LD_SONAME) -o $@ $(LIBS) $(OBJECTS)

%.o: %.c
	@echo "Compiling $<"
	@$(CC) $(CFLAGS) -c -o $@ $<


install:
	@[ -d $(LIBDIR) ] || { echo "Creating lib dir: $(LIBDIR)"; install -d $(LIBDIR); }
	@echo "Installing $(LIBRARY) into $(LIBDIR)"
	@install $(LIBRARY) $(LIBDIR)
	@echo 'Adding links'
	@cd $(LIBDIR); for link in $(LINKS); do ln -sf $(LIBRARY) $$link ; done
	@echo "Copying conf file to /usr/local/etc/nss-ega.conf"
	@cp nss-ega.conf /usr/local/etc/nss-ega.conf

clean:
	-rm -f $(LIBRARY) $(OBJECTS)
