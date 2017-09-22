#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stddef.h>
#include <security/pam_appl.h>
#include <security/pam_modules.h>
#include <security/pam_ext.h>

#include "debug.h"
#include "config.h"
#include "backend.h"

#define PAM_OPT_DEBUG			0x01
#define PAM_OPT_NO_WARN			0x02
#define PAM_OPT_USE_FIRST_PASS		0x04
#define	PAM_OPT_TRY_FIRST_PASS		0x08
#define PAM_OPT_USE_MAPPED_PASS		0x10
#define PAM_OPT_ECHO_PASS		0x20
#define PAM_OPT_TRY_OLDAUTH		0x40
#define PAM_OPT_USE_OLDAUTH		0x80

#define PAM_SM_AUTH

/* authenticate user */
PAM_EXTERN int
pam_sm_authenticate(pam_handle_t *pamh, int flags, int argc, const char **argv)
{
  const char *user, *password, *rhost;
  const void *item;
  int rc;
  const struct pam_conv *conv;
  struct pam_message msg;
  const struct pam_message *msgs[1];
  struct pam_response *resp;
  
  D("EGA %-10s: Called %s\n", __FILE__, __FUNCTION__);

  user = NULL; password = NULL; rhost = NULL;

  rc = pam_get_user(pamh, &user, NULL);
  if (rc != PAM_SUCCESS) { D("Can't get user: %s\n", pam_strerror(pamh, rc)); return rc; }
  
  rc = pam_get_item(pamh, PAM_RHOST, &item);
  if ( rc != PAM_SUCCESS) { SYSLOG("EGA: Unknown rhost: %s\n", pam_strerror(pamh, rc)); }

  if(!readconfig( (argc > 0)?argv[0]:CFGFILE )){
    D("Can't read config\n");
    return PAM_AUTH_ERR;
  }

  rhost = (char*)item;
  if(rhost){
    DBGLOG("EGA: attempting to authenticate: %s (from %s)", user, rhost);
  } else {
    DBGLOG("EGA: attempting to authenticate: %s", user);
  }

  /* Grab the already-entered password if we might want to use it. */
  if (flags & (PAM_OPT_TRY_FIRST_PASS | PAM_OPT_USE_FIRST_PASS)){
    rc = pam_get_item(pamh, PAM_AUTHTOK, &item);
    if (rc != PAM_SUCCESS){
      DBGLOG("EGA: (already-entered) password retrieval failed: %s", pam_strerror(pamh, rc));
      return rc;
    }
  }

  password = (char*)item;
  /* The user hasn't entered a password yet. */
  if (!password && (flags & PAM_OPT_USE_FIRST_PASS)){
    DBGLOG("EGA: password retrieval failed: %s", pam_strerror(pamh, rc));
    return PAM_AUTH_ERR;
  }

  /* Get the password then */
  msg.msg_style = flags & PAM_OPT_ECHO_PASS ? PAM_PROMPT_ECHO_ON : PAM_PROMPT_ECHO_OFF;
  msg.msg = options->pam_prompt;
  msgs[0] = &msg;

  rc = pam_get_item(pamh, PAM_CONV, &item);
  if (rc != PAM_SUCCESS){
    DBGLOG("EGA: conversation initialization failed: %s", pam_strerror(pamh, rc));
    return rc;
  }

  conv = (struct pam_conv *)item;
  rc = conv->conv(1, msgs, &resp, conv->appdata_ptr);
  if (rc != PAM_SUCCESS){
    DBGLOG("EGA: password conversation failed: %s", pam_strerror(pamh, rc));
    return rc;
  }
  
  rc = pam_set_item(pamh, PAM_AUTHTOK, (const void*)resp[0].resp);
  if (rc != PAM_SUCCESS){
    DBGLOG("EGA: setting password for other modules failed: %s", pam_strerror(pamh, rc));
    return rc;
  }

  /* Cleaning the message */
  memset(resp[0].resp, 0, strlen(resp[0].resp));
  free(resp[0].resp);
  free(resp);

  rc = pam_get_item(pamh, PAM_AUTHTOK, &item);
  password = (char*)item;
  if (rc != PAM_SUCCESS){
    SYSLOG("EGA: password retrieval failed: %s", pam_strerror(pamh, rc));
    return rc;
  }

  /* Check if empty password are disallowed */
  if ((!password || !*password) && (flags & PAM_DISALLOW_NULL_AUTHTOK)) { return PAM_AUTH_ERR; }
  
  /* Now, we have the password */
  if(backend_authenticate(user, password)){
    if(rhost){
      SYSLOG("EGA: user %s authenticated (from %s)", user, rhost);
    } else {
      SYSLOG("EGA: user %s authenticated", user);
    }
    return PAM_SUCCESS;
  }

  return PAM_AUTH_ERR;
}

PAM_EXTERN int
pam_sm_setcred(pam_handle_t *pamh, int flags, int argc, const char **argv)
{
  D("EGA %-10s: Called %s\n", __FILE__, __FUNCTION__);
  return PAM_SUCCESS;
}

/* check if account has expired */
PAM_EXTERN int
pam_sm_acct_mgmt(pam_handle_t *pamh, int flags, int argc,
		 const char **argv)
{
  D("EGA %-10s: Called %s\n", __FILE__, __FUNCTION__);
  return PAM_SUCCESS;
  /* modopt_t *options = NULL; */
  /* const char *user, *rhost; */
  /* int rc = PAM_AUTH_ERR; */
  /* PGconn *conn; */
  /* PGresult *res; */

  /* user = NULL; rhost = NULL; */

  /* if ((options = mod_options(argc, argv)) != NULL) { */

  /*   /\* query not specified, just succeed. *\/ */
  /*   if (options->query_acct == NULL) { */
  /*     //free_module_options(options); */
  /*     return PAM_SUCCESS; */
  /*   } */

  /*   if ((rc = pam_get_item(pamh, PAM_RHOST, (const void **)&rhost)) == PAM_SUCCESS) { */
  /*     if((rc = pam_get_user(pamh, &user, NULL)) == PAM_SUCCESS) { */
  /* 	if(!(conn = db_connect(options))) { */
  /* 	  rc = PAM_AUTH_ERR; */
  /* 	} else { */
  /* 	  DBGLOG("query: %s", options->query_acct); */
  /* 	  rc = PAM_AUTH_ERR; */
  /* 	  if(pg_execParam(conn, &res, options->query_acct, pam_get_service(pamh), user, NULL, rhost) == PAM_SUCCESS) { */
  /* 	    if (PQntuples(res) == 1 && */
  /* 		PQnfields(res) >= 2 && PQnfields(res) <= 3) { */
  /* 	      char *expired_db = PQgetvalue(res, 0, 0); */
  /* 	      char *newtok_db = PQgetvalue(res, 0, 1); */
  /* 	      rc = PAM_SUCCESS; */
  /* 	      if (PQnfields(res)>=3) { */
  /* 		char *nulltok_db = PQgetvalue(res, 0, 2); */
  /* 		if ((!strcmp(nulltok_db, "t")) && (flags & PAM_DISALLOW_NULL_AUTHTOK)) */
  /* 		  rc = PAM_NEW_AUTHTOK_REQD; */
  /* 	      } */
  /* 	      if (!strcmp(newtok_db, "t")) */
  /* 		rc = PAM_NEW_AUTHTOK_REQD; */
  /* 	      if (!strcmp(expired_db, "t")) */
  /* 		rc = PAM_ACCT_EXPIRED; */
  /* 	    } else { */
  /* 	      DBGLOG("query_acct should return one row and two or three columns"); */
  /* 	      rc = PAM_PERM_DENIED; */
  /* 	    } */
  /* 	    PQclear(res); */
  /* 	  } */
  /* 	  PQfinish(conn); */
  /* 	} */
  /*     } */
  /*   } */
  /* } */

  /* return rc; */
}

/* Check if homefolder is there. */
PAM_EXTERN int
pam_sm_open_session(pam_handle_t *pamh, int flags, int argc, const char **argv)
{
  const char *user;
  int rc;
  D("EGA %-10s: Called %s\n", __FILE__, __FUNCTION__);
  rc = pam_get_user(pamh, &user, NULL);
  if ( rc != PAM_SUCCESS) { SYSLOG("EGA: Unknown user: %s\n", pam_strerror(pamh, rc)); return rc; }
  DBGLOG("Opening Session for user: %s", user);
  return PAM_SUCCESS;
  /* const char *user, *rhost; */
  /* int rc; */

  /* user = NULL; rhost = NULL; */

  /* if ((options = mod_options(argc, argv)) != NULL) { */

  /*   if (options->query_session_open) { */

  /*     if ((rc = pam_get_item(pamh, PAM_RHOST, (const void **)&rhost)) == PAM_SUCCESS) { */

  /* 	if ((rc = pam_get_user(pamh, &user, NULL)) == PAM_SUCCESS) { */
  /* 	  DBGLOG("Session opened for user: %s", user); */
  /* 	  if ((conn = db_connect(options))) { */
  /* 	    pg_execParam(conn, &res, options->query_session_open, pam_get_service(pamh), user, NULL, rhost); */
  /* 	    PQclear(res); */
  /* 	    PQfinish(conn); */
  /* 	  } */
  /* 	} */
  /*     } */
  /*   } */
  /*   ///free_module_options(options); */
  /* } */

  /* return (PAM_SUCCESS); */

}

PAM_EXTERN int
pam_sm_close_session(pam_handle_t *pamh, int flags, int argc, const char *argv[])
{
  const char *user;
  int rc;
  D("EGA %-10s: Called %s\n", __FILE__, __FUNCTION__);
  rc = pam_get_user(pamh, &user, NULL);
  if ( rc != PAM_SUCCESS) { SYSLOG("EGA: Unknown user: %s\n", pam_strerror(pamh, rc)); return rc; }
  DBGLOG("Closing Session for user: %s", user);
  return PAM_SUCCESS;
}
