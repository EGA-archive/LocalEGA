#include <nss.h>
#include <pwd.h>

#include "debug.h"
#include "backend.h"

/*
 * passwd functions
 */
enum nss_status
_nss_ega_setpwent (int stayopen)
{
  enum nss_status status = NSS_STATUS_UNAVAIL;

  D("EGA %-10s: Called %s with args (stayopen: %d)\n", __FILE__, __FUNCTION__, stayopen);
  
  if(backend_open(stayopen)) {
    status = NSS_STATUS_SUCCESS;
  }

  /* if(!stayopen) backend_close(); */
  return status;
}

enum nss_status
_nss_ega_endpwent(void)
{
  D("EGA %-10s: Called %s\n", __FILE__, __FUNCTION__);
  backend_close();
  return NSS_STATUS_SUCCESS;
}

/* Not allowed */
enum nss_status
_nss_ega_getpwent_r(struct passwd *result,
		    char *buffer, size_t buflen,
		    int *errnop)
{
  D("EGA %-10s: Called %s\n", __FILE__, __FUNCTION__);
  return NSS_STATUS_UNAVAIL;
}

/*
  Non-Reentrant, but simultaneous calls to this function will not try
  to write the retrieved data in the same place.
  ie different 'struct passwd *result'
*/
enum nss_status
_nss_ega_getpwnam_r(const char *username,
		    struct passwd *result,
		    char *buffer, size_t buflen,
		    int *errnop)
{
  D("EGA %-10s: Called %s with args (username: %s)\n", __FILE__, __FUNCTION__, username);
  return backend_get_userentry(username, result, &buffer, &buflen, errnop);
}

/*
 * Finally: No group functions here
 */
