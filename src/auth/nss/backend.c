
#include "nss-ega.h"
#include <libpq-fe.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <errno.h>


static PGconn *_conn = NULL;
static int _isopen = 0;

/*
 * read configuration and connect to database
 */
int backend_open()
{
  int config;

  if(!_isopen) {
    config = readconfig(CFGFILE);
    if (config == 0) {
      if (_conn != NULL) {
	PQfinish(_conn);
      }
      _conn = PQconnectdb(getcfg("connection"));
    }
	  
    if(PQstatus(_conn) == CONNECTION_OK) {
      ++_isopen;
    } else {
      print_msg("\nCould not connect to database\n");
    }
  }
  return (_isopen > 0);
}

/*
 * close connection to database and clean up configuration
 */
void backend_close()
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
	return copy_attr_string(sptr, valptr, buffer, buflen, errnop);
}

/*
  With apologies to nss_ldap...
  Assign a single value to *valptr from the specified row in the result
*/
enum nss_status
copy_attr_string(char *sptr, char **valptr,
                 char **buffer, size_t *buflen, int *errnop)
{

	size_t slen;

	slen = strlen(sptr);
	if(*buflen < slen + 1) {
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
	char* tmp, homes, query;
	if(!PQntuples(res)) {
		goto BAIL_OUT;
	}

	// Carefully copy attributes into buffer.  Return NSS_STATUS_TRYAGAIN if not enough room.
	// Must return passwd_name, passwd_passwd
	status = copy_attr_colnum(res, 0, &result->pw_name, &buffer, &buflen, errnop, 0);
	if(status != NSS_STATUS_SUCCESS) goto BAIL_OUT;

	status = copy_attr_colnum(res, 1, &result->pw_passwd, &buffer, &buflen, errnop, 0);
	if(status != NSS_STATUS_SUCCESS) goto BAIL_OUT;

	// almost Fixed params
	homes = getcfg("ega_homes");
	tmp = malloc(strlen(homes) + strlen(result->pw_name) + 1);
	strcpy(tmp, homes);
	strcat(tmp, result->pw_name);
	result->pw_dir = tmp;

	result->pw_gecos = getcfg("ega_gecos");

	result->pw_uid = (uid_t) strtoul(getcfg("ega_uid"), (char**)NULL, 10);

	result->pw_gid = (gid_t) strtoul(getcfg("ega_gid"), (char**)NULL, 10);

	result->pw_shell = getcfg("ega_shell");

	DBGLOG("Converted a res to a pwd:");
	DBGLOG("UID: %d", result->pw_uid);
	DBGLOG("GID: %d", result->pw_gid);
	DBGLOG("Name: %s", result->pw_name);
	DBGLOG("Password: %s", result->pw_passwd);
	DBGLOG("Gecos: %s", result->pw_gecos);
	DBGLOG("Dir: %s", result->pw_dir);
	DBGLOG("Shell: %s", result->pw_shell);

BAIL_OUT:
	return status;
}

/*
 * backend for getpwnam()
 */
enum nss_status backend_getpwnam(const char *name,
				 struct passwd *result,
                                 char *buffer,
				 size_t buflen,
				 int *errnop)
{
	const char *params[1];
	PGresult *res;
	enum nss_status status = NSS_STATUS_NOTFOUND;

	params[0] = name;

	res = PQexecParams(_conn, getcfg("ega_query"), 1, NULL, params, NULL, NULL, 0);
	if(PQresultStatus(res) == PGRES_TUPLES_OK) {
		// Fill result structure with data from the database
		status = res2pwd(res, result, buffer, buflen, errnop);
	}

	PQclear(res);
	return status;
}

/*
 * backend for getpwuid()
 */
enum nss_status backend_getpwuid(uid_t uid,
				 struct passwd *result,
				 char *buffer,
				 size_t buflen,
				 int *errnop)
{
	char *params[1];
	int n;
	PGresult *res;
	enum nss_status status = NSS_STATUS_NOTFOUND;
   
   	params[0] = malloc(12);
	n = snprintf(params[0], 12, "%d", uid);
	if (n == -1 || n > 12) {
		status = NSS_STATUS_UNAVAIL;
		*errnop = EAGAIN;
	} else {
		res = PQexecParams(_conn, getcfg("getuser"), 1, NULL, (const char**)params, NULL, NULL, 0);

		if(PQresultStatus(res) == PGRES_TUPLES_OK) {
			// Fill result structure with data from the database
			status = res2pwd(res, result, buffer, buflen, errnop);
		}
		PQclear(res);
    }
	free(params[0]);
	return status;
}
