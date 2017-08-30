
#include "nss-ega.h"
#include <libpq-fe.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <errno.h>

/* define passwd column names */
#define PASSWD_NAME   0
#define PASSWD_PASSWD 1
#define PASSWD_UID    2
#define PASSWD_GID    3
#define PASSWD_GECOS  4
#define PASSWD_DIR    5
#define PASSWD_SHELL  6

static PGconn *_conn = NULL;
static int _isopen = 0;

/*
 * read configuration and connect to database
 */
int backend_isopen(void)
{
  return (_isopen > 0);
}

int backend_open(void)
{
  int config;
  char* connection;

  if(!_isopen) {
    config = readconfig(CFGFILE);
    if (config == 0) {
      if (_conn != NULL) {
	PQfinish(_conn);
      }
      connection = getcfg("connection");
      DBGLOG("Connection to: %s",connection);
      _conn = PQconnectdb(connection);
    }
	  
    if(PQstatus(_conn) == CONNECTION_OK) {
      ++_isopen;
    } else {
      SYSLOG("Could not connect to database");
    }
  }
  return (_isopen > 0);
}

/*
 * close connection to database and clean up configuration
 */
void backend_close(void)
{
  --_isopen;
  if(!_isopen) {
    PQfinish(_conn);
    _conn = NULL;
  }
  if(_isopen < 0) {
    _isopen = 0;
  }
}

/*
  With apologies to nss_ldap...
  Assign a single value to *valptr from the specified row in the result
*/
enum nss_status
copy_attr_colnum(PGresult *res, int attrib_number, char **valptr,
                 char **buffer, size_t *buflen, int *errnop, int row)
{

  const char *sptr;
  size_t slen;

  sptr = PQgetvalue(res, row, attrib_number);
  slen = strlen(sptr);
  if(*buflen < slen+1) {
    *errnop = ERANGE;
    return NSS_STATUS_TRYAGAIN;
  }
  strncpy(*buffer, sptr, slen);
  (*buffer)[slen] = '\0';
  
  *valptr = *buffer;
  
  *buffer += slen + 1;
  *buflen -= slen + 1;
  
  return NSS_STATUS_SUCCESS;
}

/*
 * 'convert' a PGresult to struct passwd
 */
enum nss_status res2pwd(PGresult *res, struct passwd *result,
                        char *buffer, size_t buflen,
			int *errnop)
{
  enum nss_status status = NSS_STATUS_NOTFOUND;
  if(!PQntuples(res)) {
    goto BAIL_OUT;
  }

  status = copy_attr_colnum(res, PASSWD_NAME, &result->pw_name, &buffer, &buflen, errnop, 0);
  if(status != NSS_STATUS_SUCCESS) goto BAIL_OUT;

  status = copy_attr_colnum(res, PASSWD_PASSWD, &result->pw_passwd, &buffer, &buflen, errnop, 0);
  if(status != NSS_STATUS_SUCCESS) goto BAIL_OUT;

  status = copy_attr_colnum(res, PASSWD_GECOS, &result->pw_gecos, &buffer, &buflen, errnop, 0);
  if(status != NSS_STATUS_SUCCESS) goto BAIL_OUT;

  status = copy_attr_colnum(res, PASSWD_DIR, &result->pw_dir, &buffer, &buflen, errnop, 0);
  if(status != NSS_STATUS_SUCCESS) goto BAIL_OUT;

  status = copy_attr_colnum(res, PASSWD_SHELL, &result->pw_shell, &buffer, &buflen, errnop, 0);
  if(status != NSS_STATUS_SUCCESS) goto BAIL_OUT;

  // Can be less careful with uid/gid
  result->pw_uid = (uid_t) strtoul(PQgetvalue(res, 0, PASSWD_UID), (char**)NULL, 10);
  result->pw_gid = (gid_t) strtoul(PQgetvalue(res, 0, PASSWD_GID), (char**)NULL, 10);

#ifdef DEBUG
  DBGLOG("Converted a res to a pwd:");
  DBGLOG("UID: %d", result->pw_uid);
  DBGLOG("GID: %d", result->pw_gid);
  DBGLOG("Name: %s", result->pw_name);
  DBGLOG("Password: %s", result->pw_passwd);
  DBGLOG("Gecos: %s", result->pw_gecos);
  DBGLOG("Dir: %s", result->pw_dir);
  DBGLOG("Shell: %s", result->pw_shell);
#endif

BAIL_OUT:
  return status;
}

/*
 * backend for getpwnam()
 */
enum nss_status backend_getpwnam(const char *name,
				 struct passwd *result,
                                 char *buffer, size_t buflen,
				 int *errnop)
{
  const char *params[1];
  PGresult *res;
  enum nss_status status = NSS_STATUS_NOTFOUND;

  params[0] = name;

  res = PQexecParams(_conn, getcfg("getpwnam"), 1, NULL, params, NULL, NULL, 0);
  if(PQresultStatus(res) == PGRES_TUPLES_OK) {
    // Fill result structure with data from the database
    status = res2pwd(res, result, buffer, buflen, errnop);
  }

  PQclear(res);
  return status;
}

/*
 * get a passwd entry from cursor
 */
enum nss_status
backend_getpwent(struct passwd *result,
		 char *buffer, size_t buflen,
		 int *errnop)
{
  /* PGresult *res; */
  enum nss_status status = NSS_STATUS_NOTFOUND;

  /* res = PQexecParams(_conn, getcfg("getpwent"), 1, NULL, params, NULL, NULL, 0); */
  /* if(PQresultStatus(res) == PGRES_TUPLES_OK) { */
  /*   status = res2pwd(res, result, buffer, buflen, errnop); */
  /* } */
  /* PQclear(res); */
  return status;
}   

/*
 * backend for getpwuid(): Unused
 */
enum nss_status
backend_getpwuid(uid_t uid,
		 struct passwd *result,
		 char *buffer, size_t buflen,
		 int *errnop)
{
  return NSS_STATUS_NOTFOUND;
}
