#ifndef __NSS_EGA_H_INCLUDED__
#define __NSS_EGA_H_INCLUDED__

/* #include <unistd.h> */
#include <nss.h>
#include <pwd.h>
#include <sys/types.h>

#define CFGFILE "/usr/local/etc/nss-ega.conf"

int readconfig(char* configfile);
void cleanup(void);
char* getcfg(const char* key);

int backend_isopen();
int backend_open();
void backend_close();

enum nss_status backend_getpwuid(uid_t uid,
				 struct passwd *result,
				 char *buffer,
				 size_t buflen,
				 int *errnop);
enum nss_status backend_getpwnam(const char *name,
				 struct passwd *result,
				 char *buffer,
				 size_t buflen,
				 int *errnop);

#ifdef DEBUG
#include <syslog.h>
#define DBGLOG(x...)  do {                                          \
                          openlog("NSS_pgsql", LOG_PID, LOG_AUTH);  \
                          syslog(LOG_DEBUG, ##x);                   \
                          closelog();                               \
                      } while(0);
#define SYSLOG(x...)  do {                                          \
                          openlog("NSS_pgsql", LOG_PID, LOG_AUTH);  \
                          syslog(LOG_INFO, ##x);                    \
                          closelog();                               \
                      } while(0);
#else
#define DBGLOG(x...)
#define SYSLOG(x...)
#endif /* !DEBUG */

#endif /* !__NSS_PGSQL_H_INCLUDED__ */
