#ifndef __LEGA_CONFIG_H_INCLUDED__
#define __LEGA_CONFIG_H_INCLUDED__

#include <stdbool.h>

#define CFGFILE "/etc/ega/auth.conf"
#define ENABLE_REST false
#define BUFFER_REST 1024

struct options_s {
  bool debug;
  char* cfgfile;

  /* Database cache connection */
  char* db_connstr;

  /* NSS queries */
  char* nss_user_entry; /* SELECT elixir_id,'x',<uid>,<gid>,'EGA User','/ega/inbox/'|| elixir_id,'/bin/bash' FROM users WHERE elixir_id = $1 */

  /* PAM queries */
  char* pam_auth;       /* SELECT password_hash FROM users WHERE elixir_id = $1 */
  char* pam_acct;       /* SELECT password_hash FROM users WHERE elixir_id = $1 */

  int pam_flags;        /* PAM module flags, like debug of conf_file */

  /* ReST location */
  bool with_rest;        /* enable the lookup in case the entry is not found in the database cache */
  char* rest_endpoint;   /* https://ega/user/<some-id> | returns a triplet in JSON format */
  int rest_buffer_size;  /* 1024 */
};

typedef struct options_s options_t;

extern options_t* options;

bool readconfig(char* configfile);
void cleanconfig(void);

#endif /* !__LEGA_CONFIG_H_INCLUDED__ */
