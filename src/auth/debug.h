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

#define D(x...)  fprintf(stderr, ##x);
#undef DBGLOG
#undef SYSLOG
#undef AUTHLOG
#define DBGLOG(x...) do { fprintf(stderr, ##x); fprintf(stderr, "\n"); } while(0);
#define SYSLOG(x...) do { fprintf(stderr, ##x); fprintf(stderr, "\n"); } while(0);
#define AUTHLOG(x...) do { fprintf(stderr, ##x); fprintf(stderr, "\n"); } while(0);

#else

#define D(x...)

#endif /* !DEBUG */

#endif /* !__LEGA_DEBUG_H_INCLUDED__ */
