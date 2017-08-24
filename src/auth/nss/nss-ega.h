#ifndef __NSS_EGA_H_INCLUDED__
#define __NSS_EGA_H_INCLUDED__

#include <stdio.h>
#include <stdlib.h>
/* #include <unistd.h> */
#include <nss.h>
#include <pwd.h>
#include <sys/types.h>
#ifdef DEBUG
#include <syslog.h>
#endif

#define CFGFILE "/usr/local/etc/nss-ega.conf"

int readconfig(char* configfile);
void cleanup(void);
char* getcfg(const char* key);

int backend_isopen(void);
int backend_open(void);
void backend_close(void);

enum nss_status backend_getpwuid(uid_t uid,
				 struct passwd *result,
				 char *buffer, size_t buflen,
				 int *errnop);
  
enum nss_status backend_getpwnam(const char *name,
				 struct passwd *result,
				 char *buffer, size_t buflen,
				 int *errnop);

enum nss_status backend_getpwent(struct passwd *result,
				 char *buffer, size_t buflen,
				 int *errnop);


#ifdef DEBUG
#define DBGLOG(x...)  do {                                          \
                          openlog("NSS_ega", LOG_PID, LOG_USER);    \
                          syslog(LOG_DEBUG, ##x);                   \
                          closelog();                               \
                      } while(0);
#define SYSLOG(x...)  do {                                          \
                          openlog("NSS_ega", LOG_PID, LOG_USER);    \
                          syslog(LOG_AUTHPRIV, ##x);                \
                          closelog();                               \
                      } while(0);
#else
#define DBGLOG(x...)
#define SYSLOG(x...)
#endif /* !DEBUG */

#endif /* !__NSS_PGSQL_H_INCLUDED__ */

