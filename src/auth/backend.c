#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <errno.h>
#include <libpq-fe.h>


#include "debug.h"
#include "config.h"
#include "backend.h"
#include "cega.h"

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
  D("called with args: stayopen: %d\n", stayopen);
  if(!readconfig(CFGFILE)){
    D("%s", "Can't read config");
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
  D("%s", "called");
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
enum nss_status
get_from_db(const char* username, struct passwd *result, char **buffer, size_t *buflen, int *errnop)
{
  enum nss_status status = NSS_STATUS_NOTFOUND;
  const char* params[1] = { username };
  PGresult *res;

  D("Prepared Statement: %s\n", options->nss_get_user);
  D("with '%s'\n", username);
  res = PQexecParams(conn, options->nss_get_user, 1, NULL, params, NULL, NULL, 0);

  if(PQresultStatus(res) != PGRES_TUPLES_OK) goto BAIL_OUT;

  if(!PQntuples(res)) goto BAIL_OUT; /* Answer is not a tuple: User not found */

  /* no error, let's convert the result to a struct pwd */
  status = _res2pwd(res, 0, COL_NAME, &(result->pw_name), buffer, buflen, errnop);
  if(status != NSS_STATUS_SUCCESS) return status;

  status = _res2pwd(res, 0, COL_PASSWD, &(result->pw_passwd), buffer, buflen, errnop);
  if(status != NSS_STATUS_SUCCESS) return status;

  status = _res2pwd(res, 0, COL_GECOS, &(result->pw_gecos), buffer, buflen, errnop);
  if(status != NSS_STATUS_SUCCESS) return status;

  status = _res2pwd(res, 0, COL_DIR, &(result->pw_dir), buffer, buflen, errnop);
  if(status != NSS_STATUS_SUCCESS) return status;

  status = _res2pwd(res, 0, COL_SHELL, &(result->pw_shell), buffer, buflen, errnop);
  if(status != NSS_STATUS_SUCCESS) return status;

  result->pw_uid = (uid_t) strtoul(PQgetvalue(res, 0, COL_UID), (char**)NULL, 10);
  result->pw_gid = (gid_t) strtoul(PQgetvalue(res, 0, COL_GID), (char**)NULL, 10);

  status = NSS_STATUS_SUCCESS;

BAIL_OUT:
  PQclear(res);
  return status;
}

bool
add_to_db(const char* username, const char* pwdh, const char* pubkey)
{
  const char* params[3] = { username, pwdh, pubkey};
  PGresult *res;
  bool success;

  D("Prepared Statement: %s\n", options->nss_add_user);
  D("with VALUES('%s','%s','%s')\n", username, pwdh, pubkey);
  res = PQexecParams(conn, options->nss_add_user, 3, NULL, params, NULL, NULL, 0);

  success = (PQresultStatus(res) == PGRES_TUPLES_OK);
  if(!success) D("%s\n", PQerrorMessage(conn));
  PQclear(res);
  return success;
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
  D("called\n");

  if(!backend_open(0)) return NSS_STATUS_UNAVAIL;

  if( get_from_db(username, result, buffer, buflen, errnop) )
    return NSS_STATUS_SUCCESS;

  /* OK, User not found in DB */

  /* if REST disabled */
  if(!options->with_rest){
    D("contacting cega for user: %s is disabled\n", username);
    return NSS_STATUS_NOTFOUND;
  }
    
  if(!fetch_from_cega(username, buffer, buflen, errnop))
    return NSS_STATUS_NOTFOUND;

  /* User retrieved from Central EGA, try again the DB */
  if( get_from_db(username, result, buffer, buflen, errnop) )
    return NSS_STATUS_SUCCESS;

  /* No luck, user not found */
  return NSS_STATUS_NOTFOUND;
}

bool
backend_authenticate(const char *user, const char *password)
{
  return false;
}
