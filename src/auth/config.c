#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <errno.h>
#include <ctype.h>

#include "debug.h"
#include "config.h"

options_t* options = NULL;

void
cleanconfig(void)
{
  if(!options) return;

  SYSLOG("Cleaning the config struct");
  /* if(!options->cfgfile           ) { free(options->cfgfile);        } */
  if(!options->db_connstr        ) { free((char*)options->db_connstr);     }
  if(!options->nss_get_user      ) { free((char*)options->nss_get_user);   }
  if(!options->nss_add_user      ) { free((char*)options->nss_add_user);   }
  if(!options->pam_auth          ) { free((char*)options->pam_auth);       }
  if(!options->pam_acct          ) { free((char*)options->pam_acct);       }
  if(!options->pam_prompt        ) { free((char*)options->pam_prompt);     }
  if(!options->rest_endpoint     ) { free((char*)options->rest_endpoint);  }
  if(!options->rest_user         ) { free((char*)options->rest_user);      }
  if(!options->rest_password     ) { free((char*)options->rest_password);  }
  if(!options->rest_resp_passwd  ) { free((char*)options->rest_resp_passwd); }
  if(!options->rest_resp_pubkey  ) { free((char*)options->rest_resp_pubkey); }
  if(!options->ssl_cert          ) { free((char*)options->ssl_cert);       }
  if(!options->skel              ) { free((char*)options->skel);           }
  free(options);
  return;
}

bool
readconfig(const char* configfile)
{

  FILE* fp;
  char* line = NULL;
  size_t len = 0;
  char *key,*eq,*val,*end;

  D("called (cfgfile: %s)\n", configfile);

  if(options) return true; /* Done already */

  SYSLOG("Loading configuration %s", configfile);

  /* read or re-read */
  fp = fopen(configfile, "r");
  if (fp == NULL || errno == EACCES) {
    SYSLOG("Error accessing the config file: %s", strerror(errno));
    cleanconfig();
    return false;
  }
      
  options = (options_t*)malloc(sizeof(options_t));
      
  /* Default config values */
  options->cfgfile = configfile;
  options->with_rest = ENABLE_REST;
  options->rest_buffer_size = BUFFER_REST;
  options->pam_prompt = PAM_PROMPT;
  options->ssl_cert = CEGA_CERT;
  options->with_homedir = false;
  options->skel = "/ega/skel";

  options->rest_resp_passwd = ".password";
  options->rest_resp_pubkey = ".pubkey";
      
  /* Parse line by line */
  while (getline(&line, &len, fp) > 0) {
	
    key=line;
    /* remove leading whitespace */
    while(isspace(*key)) key++;
      
    if((eq = strchr(line, '='))) {
      end = eq - 1; /* left of = */
      val = eq + 1; /* right of = */
	  
      /* find the end of the left operand */
      while(end > key && isspace(*end)) end--;
      *(end+1) = '\0';
	  
      /* find where the right operand starts */
      while(*val && isspace(*val)) val++;
	  
      /* find the end of the right operand */
      eq = val;
      while(*eq != '\0') eq++;
      eq--;
      if(*eq == '\n') { *eq = '\0'; } /* remove new line */
	  
    } else val = NULL; /* could not find the '=' sign */
	
    if(!strcmp(key, "debug"             )) { options->debug = true;                 }
    if(!strcmp(key, "db_connection"     )) { options->db_connstr = strdup(val);     }
    if(!strcmp(key, "nss_get_user"      )) { options->nss_get_user = strdup(val);   }
    if(!strcmp(key, "nss_add_user"      )) { options->nss_add_user = strdup(val);   }
    if(!strcmp(key, "pam_auth"          )) { options->pam_auth = strdup(val);       }
    if(!strcmp(key, "pam_acct"          )) { options->pam_acct = strdup(val);       }
    if(!strcmp(key, "pam_prompt"        )) { options->pam_prompt = strdup(val);     }
    if(!strcmp(key, "skel"              )) { options->skel = strdup(val);           }
    if(!strcmp(key, "rest_endpoint"     )) { options->rest_endpoint = strdup(val);  }
    if(!strcmp(key, "rest_user"         )) { options->rest_user     = strdup(val);  }
    if(!strcmp(key, "rest_password"     )) { options->rest_password = strdup(val);  }
    if(!strcmp(key, "rest_resp_passwd"  )) { options->rest_resp_passwd=strdup(val); }
    if(!strcmp(key, "rest_resp_pubkey"  )) { options->rest_resp_pubkey=strdup(val); }
    if(!strcmp(key, "rest_buffer_size"  )) { options->rest_buffer_size = atoi(val); }
    if(!strcmp(key, "ssl_cert"          )) { options->ssl_cert = strdup(val);       }
    if(!strcmp(key, "enable_rest")) {
      if(!strcmp(val, "yes") || !strcmp(val, "true")){
	options->with_rest = true;
      } else {
	SYSLOG("Could not parse the enable_rest: Using %s instead.", ((options->with_rest)?"yes":"no"));
      }
    }
    if(!strcmp(key, "with_homedir")) {
      if(!strcmp(val, "yes") || !strcmp(val, "true")){
	options->with_homedir = true;
      } else {
	SYSLOG("Could not parse the with_homedir: Using %s instead.", ((options->with_homedir)?"yes":"no"));
      }
    }
	
  }

  fclose(fp);
  if (line) { free(line); }

  D("options: %p\n", options);
  return true;
}
