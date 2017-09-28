#ifndef __LEGA_CONFIG_H_INCLUDED__
#define __LEGA_CONFIG_H_INCLUDED__

#include <stdbool.h>

#define CFGFILE "/etc/ega/auth.conf"
#define ENABLE_REST false
#define BUFFER_REST 1024
#define CEGA_CERT "/etc/ega/cega.pem"
#define PAM_PROMPT "Please, enter your EGA password: "

struct options_s {
  bool debug;
  const char* cfgfile;
  
  /* Database cache connection */
  char* db_connstr;

  /* NSS queries */
  const char* nss_get_user; /* SELECT elixir_id,'x',<uid>,<gid>,'EGA User','/ega/inbox/'|| elixir_id,'/bin/bash' FROM users WHERE elixir_id = $1 */
  const char* nss_add_user; /* INSERT INTO users (elixir_id, password_hash, pubkey) VALUES($1,$2,$3) */

  /* PAM queries */
  const char* pam_auth;       /* SELECT password_hash FROM users WHERE elixir_id = $1 */
  const char* pam_acct;       /* SELECT password_hash FROM users WHERE elixir_id = $1 */
  const char* pam_prompt;     /* Please enter password */

  int pam_flags;        /* PAM module flags, like debug of conf_file */

  /* ReST location */
  bool with_rest;             /* enable the lookup in case the entry is not found in the database cache */
  const char* rest_endpoint;  /* https://ega/user/<some-id> | returns a triplet in JSON format */
  int rest_buffer_size;       /* 1024 */
  const char* ssl_cert;       /* path the SSL certificate to contact Central EGA */

  /* For the Homedir creation */
  bool with_homedir;          /* enable the homedir creation */
  const char* skel;           /* path to skeleton dir */
};

typedef struct options_s options_t;

extern options_t* options;

bool readconfig(const char* configfile);
void cleanconfig(void);
    
#endif /* !__LEGA_CONFIG_H_INCLUDED__ */
