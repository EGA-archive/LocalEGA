#
# Makefile for the NSS and PAM modules used in Local EGA
#
# Blowfish code from http://www.openwall.com/crypt/
#

NSS_LD_SONAME=-Wl,-soname,libnss_ega.so.2
NSS_LIBRARY=libnss_ega.so.2.0
PAM_LIBRARY = pam_ega.so

CC=gcc
LD=ld
AS=gcc -c
CFLAGS=-Wall -Wstrict-prototypes -Werror -fPIC -O2 -I. -I$(shell pg_config --includedir)
LIBS=-lpq -lpam -lcurl -ljq -L$(shell pg_config --libdir)

LIBDIR=/usr/local/lib/ega

HEADERS = debug.h config.h backend.h cega.h homedir.h $(wildcard blowfish/*.h)

NSS_SOURCES = nss.c config.c backend.c cega.c homedir.c
NSS_OBJECTS = $(NSS_SOURCES:%.c=%.o)

PAM_SOURCES = pam.c config.c backend.c cega.c homedir.c $(wildcard blowfish/*.c)
PAM_OBJECTS = $(PAM_SOURCES:%.c=%.o) blowfish/x86.o

.PHONY: clean install
.SUFFIXES: .c .o .S .so .so.2 .so.2.0

all: install

debug: CFLAGS += -DDEBUG -g
debug: install

$(NSS_LIBRARY): $(HEADERS) $(NSS_OBJECTS)
	@echo "Linking objects into $@"
	@$(CC) -shared $(NSS_LD_SONAME) -o $@ $(LIBS) $(NSS_OBJECTS)

$(PAM_LIBRARY): $(HEADERS) $(PAM_OBJECTS)
	@echo "Linking objects into $@"
	@$(LD) -x --shared -o $@ $(LIBS) $(PAM_OBJECTS)

blowfish/x86.o: blowfish/x86.S $(HEADERS)
	@echo "Compiling $<"
	@$(CC) -c -o $@ $<

%.o: %.c $(HEADERS)
	@echo "Compiling $<"
	@$(CC) $(CFLAGS) -c -o $@ $<

install-nss: $(NSS_LIBRARY)
	@[ -d $(LIBDIR) ] || { echo "Creating lib dir: $(LIBDIR)"; install -d $(LIBDIR); }
	@echo "Installing $< into $(LIBDIR)"
	@install $< $(LIBDIR)

install-pam: $(PAM_LIBRARY)
	@[ -d $(LIBDIR) ] || { echo "Creating lib dir: $(LIBDIR)"; install -d $(LIBDIR); }
	@echo "Installing $< into $(LIBDIR)"
	@install $< $(LIBDIR)

install: install-nss install-pam
	@echo "Do not forget to run ldconfig and create/configure the file /etc/ega/auth.conf"
	@echo "Look at the auth.conf.sample here, for example"


clean:
	-rm -f $(NSS_LIBRARY) $(NSS_OBJECTS)
	-rm -f $(PAM_LIBRARY) $(PAM_OBJECTS)
