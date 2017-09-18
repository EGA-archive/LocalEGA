#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <errno.h>
#include <libpq-fe.h>

#include "debug.h"
#include "config.h"
#include "backend.h"

/* define passwd column names */
#define COL_NAME   0
#define COL_PASSWD 1
#define COL_UID    2
#define COL_GID    3
#define COL_GECOS  4
#define COL_DIR    5
#define COL_SHELL  6

static PGconn* conn;

/* connect to database */
bool
backend_open(int stayopen)
{
  D("EGA %-10s: Called %s (stayopen: %d)\n", __FILE__, __FUNCTION__, stayopen);
  if(!readconfig(CFGFILE)){
    D("Can't read config\n");
    return false;
  }
  if(!conn){
    DBGLOG("Connection to: %s", options->db_connstr);
    conn = PQconnectdb(options->db_connstr);
  }
	  
  if(PQstatus(conn) != CONNECTION_OK) {
    SYSLOG("PostgreSQL connection failed: '%s'", PQerrorMessage(conn));
    backend_close(); /* reentrant */
    return false;
  }
  D("DB Connection: %p\n", conn);

  return true;
}


/* close connection to database */
void
backend_close(void)
{ 
  D("EGA %-10s: Called %s\n", __FILE__, __FUNCTION__);
  if (conn) PQfinish(conn);
  conn = NULL;
}

/*
  Assign a single value to *p from the specified row in the result.
  We use 'buffer' to store the result values, and increase its size if necessary.
  That way, we don't allocate strings for struct passwd
*/
enum nss_status
_res2pwd(PGresult *res, int row, int col,
	 char **p, char **buf, size_t *buflen,
	 int *errnop)
{
  const char *s;
  size_t slen;

  s = PQgetvalue(res, row, col);
  slen = strlen(s);

  if(*buflen < slen+1) {
    *errnop = ERANGE;
    return NSS_STATUS_TRYAGAIN;
  }
  strncpy(*buf, s, slen);
  (*buf)[slen] = '\0';

  *p = *buf; /* where is the value inside buffer */
  
  *buf += slen + 1;
  *buflen -= slen + 1;
  
  return NSS_STATUS_SUCCESS;
}

/*
 * 'convert' a PGresult to struct passwd
 */
enum nss_status res2pwd(PGresult *res, struct passwd *result,
                        char **buffer, size_t *buflen,
			int *errnop)
{
  enum nss_status status = NSS_STATUS_NOTFOUND;

  if(!PQntuples(res)) goto BAIL_OUT;

  status = _res2pwd(res, 0, COL_NAME, &(result->pw_name), buffer, buflen, errnop);
  if(status != NSS_STATUS_SUCCESS) goto BAIL_OUT;

  status = _res2pwd(res, 0, COL_PASSWD, &(result->pw_passwd), buffer, buflen, errnop);
  if(status != NSS_STATUS_SUCCESS) goto BAIL_OUT;

  status = _res2pwd(res, 0, COL_GECOS, &(result->pw_gecos), buffer, buflen, errnop);
  if(status != NSS_STATUS_SUCCESS) goto BAIL_OUT;

  status = _res2pwd(res, 0, COL_DIR, &(result->pw_dir), buffer, buflen, errnop);
  if(status != NSS_STATUS_SUCCESS) goto BAIL_OUT;

  status = _res2pwd(res, 0, COL_SHELL, &(result->pw_shell), buffer, buflen, errnop);
  if(status != NSS_STATUS_SUCCESS) goto BAIL_OUT;

  result->pw_uid = (uid_t) strtoul(PQgetvalue(res, 0, COL_UID), (char**)NULL, 10);
  result->pw_gid = (gid_t) strtoul(PQgetvalue(res, 0, COL_GID), (char**)NULL, 10);

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
 * Get one entry from the Postgres result
 */
enum nss_status
backend_get_userentry(const char *username,
		      struct passwd *result,
		      char **buffer, size_t *buflen,
		      int *errnop)
{
  enum nss_status status = NSS_STATUS_NOTFOUND;
  const char* params[1];
  PGresult *res;

  D("EGA %-10s: Called %s\n", __FILE__, __FUNCTION__);

  if(!backend_open(0)) return NSS_STATUS_UNAVAIL;

  D("Request: %s\n", options->nss_user_entry);

  params[0] = username;
  res = PQexecParams(conn, options->nss_user_entry, 1, NULL, params, NULL, NULL, 0);
  if(PQresultStatus(res) == PGRES_TUPLES_OK) {
    /* convert to pwd */
    status = res2pwd(res, result, buffer, buflen, errnop);
  }
  PQclear(res);
  return status;
}

// Contact CRG with REST. returns EAGAIN on failure
