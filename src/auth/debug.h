#ifndef __LEGA_DEBUG_H_INCLUDED__
#define __LEGA_DEBUG_H_INCLUDED__

#include <syslog.h>

#define DBGLOG(x...)  if(options->debug) {                          \
                          openlog("EGA_auth", LOG_PID, LOG_USER);   \
                          syslog(LOG_DEBUG, ##x);                   \
                          closelog();                               \
                      }
#define SYSLOG(x...)  do {                                          \
                          openlog("EGA_auth", LOG_PID, LOG_USER);   \
                          syslog(LOG_INFO, ##x);                    \
                          closelog();                               \
                      } while(0);
#define AUTHLOG(x...) do {                                          \
                          openlog("EGA_auth", LOG_PID, LOG_USER);   \
                          syslog(LOG_AUTHPRIV, ##x);                \
                          closelog();                               \
                      } while(0);

#ifdef DEBUG

#include <stdio.h>

#define D(x...) do { fprintf(stderr, "EGA %-10s | %4d | %22s | ", __FILE__, __LINE__, __FUNCTION__); \
	             fprintf(stderr, ##x);                                                           \
                } while(0);

/* #undef DBGLOG */
/* #undef SYSLOG */
/* #undef AUTHLOG */
/* #define DBGLOG(y...) do { D( ##y ); fprintf(stderr, "\n"); } while(0); */
/* #define SYSLOG(y...) do { D( ##y ); fprintf(stderr, "\n"); } while(0); */
/* #define AUTHLOG(y...) do { D( ##y ); fprintf(stderr, "\n"); } while(0); */

#else

#define D(x...)

#endif /* !DEBUG */

#endif /* !__LEGA_DEBUG_H_INCLUDED__ */
