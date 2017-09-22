#include <nss.h>
#include <pwd.h>
#include <string.h>

#include "debug.h"
#include "backend.h"

/*
 * passwd functions
 */
enum nss_status
_nss_ega_setpwent (int stayopen)
{
  enum nss_status status = NSS_STATUS_UNAVAIL;

  D("called with args (stayopen: %d)\n", stayopen);
  
  if(backend_open(stayopen)) {
    status = NSS_STATUS_SUCCESS;
  }

  /* if(!stayopen) backend_close(); */
  return status;
}

enum nss_status
_nss_ega_endpwent(void)
{
  D("called\n");
  backend_close();
  return NSS_STATUS_SUCCESS;
}

/* Not allowed */
enum nss_status
_nss_ega_getpwent_r(struct passwd *result,
		    char *buffer, size_t buflen,
		    int *errnop)
{
  D("called\n");
  return NSS_STATUS_UNAVAIL;
}

/* Find user ny name */
enum nss_status
_nss_ega_getpwnam_r(const char *username,
		    struct passwd *result,
		    char *buffer, size_t buflen,
		    int *errnop)
{
  /* bail out if we're looking for the root user */
  if( !strcmp(username, "root") ) return NSS_STATUS_NOTFOUND;
  if( !strcmp(username, "ega") ) return NSS_STATUS_NOTFOUND;
  D("called with args: username: %s\n", username);
  return backend_get_userentry(username, result, &buffer, &buflen, errnop);
}

/*
 * Finally: No group functions here
 */
