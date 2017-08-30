# Makefile for the NSS module used in Local EGA

LD_SONAME=-Wl,-soname,libnss_ega.so.2
LIBRARY=libnss_ega.so.2.0

CC=gcc
CFLAGS=-Wall -Wstrict-prototypes -Werror -fPIC -O2 -I. -I/usr/pgsql-9.6/include
LIBS=-pthread -lpq

LIBDIR=/usr/local/lib/ega

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
	@echo "Do not forget to run ldconfig and create/configure the file /usr/local/etc/nss-ega.conf"
	@echo "Look at the nss-ega.conf.sample here for example"

clean:
	-rm -f $(LIBRARY) $(OBJECTS)
