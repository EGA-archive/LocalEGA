#include "nss-ega.h"
#include <pthread.h>

static pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;

/*
 * passwd functions
 */
enum nss_status
_nss_ega_setpwent (void)
{
  enum nss_status retval = NSS_STATUS_UNAVAIL;

  pthread_mutex_lock(&lock);

  if(backend_open()) {
    retval = NSS_STATUS_SUCCESS;
  }

  pthread_mutex_unlock(&lock);

  return retval;
}

enum nss_status
_nss_ega_endpwent(void)
{
  pthread_mutex_lock(&lock);
  backend_close();
  pthread_mutex_unlock(&lock);
  
  return NSS_STATUS_SUCCESS;
}

enum nss_status
_nss_ega_getpwent_r(struct passwd *result,
		    char *buffer, size_t buflen,
		    int *errnop)
{
  enum nss_status retval = NSS_STATUS_UNAVAIL;
  int lerrno = 0;

  pthread_mutex_lock(&lock);

  if(backend_open()) {
    retval = backend_getpwent(result, buffer, buflen, &lerrno);
  }
  *errnop = lerrno;
  pthread_mutex_unlock(&lock);
  
  return retval;
}

enum nss_status
_nss_ega_getpwnam_r(const char *pwnam,
		    struct passwd *result,
		    char *buffer, size_t buflen,
		    int *errnop)
{
  enum nss_status retval = NSS_STATUS_UNAVAIL;
  int lerrno = 0;

  pthread_mutex_lock(&lock);
  if(backend_open()) {
    retval = backend_getpwnam(pwnam, result, buffer, buflen, &lerrno);
  }
  backend_close();
  *errnop = lerrno;
  pthread_mutex_unlock(&lock);

  return retval;
}

/*
 * group functions? No, thanks
 */
