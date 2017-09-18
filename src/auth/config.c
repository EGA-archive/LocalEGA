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
  if(!options->db_connstr        ) { free(options->db_connstr);     }
  if(!options->nss_user_entry    ) { free(options->nss_user_entry); }
  if(!options->pam_auth          ) { free(options->pam_auth);       }
  if(!options->pam_acct          ) { free(options->pam_acct);       }
  if(!options->rest_endpoint     ) { free(options->rest_endpoint);  }
  free(options);
  return;
}

bool
readconfig(char* configfile)
{

  FILE* fp;
  char* line = NULL;
  size_t len = 0;
  char *key,*eq,*val,*end;

  D("EGA %-10s: Called %s (cfgfile: %s)\n", __FILE__, __FUNCTION__, configfile);

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
    if(!strcmp(key, "nss_user_entry"    )) { options->nss_user_entry = strdup(val); }
    if(!strcmp(key, "pam_auth"          )) { options->pam_auth = strdup(val);       }
    if(!strcmp(key, "pam_acct"          )) { options->pam_acct = strdup(val);       }
    if(!strcmp(key, "rest_endpoint"     )) { options->rest_endpoint = strdup(val);  }
    if(!strcmp(key, "rest_buffer_size"  )) { options->rest_buffer_size = atoi(val); }
    if(!strcmp(key, "enable_rest")) {
      if(!strcmp(val, "yes") || !strcmp(val, "true")){
	options->with_rest = true;
      } else {
	SYSLOG("Could not parse the enable_rest: Using %s instead.", ((options->with_rest)?"yes":"no"));
      }
    }
	
  }

  fclose(fp);
  if (line) { free(line); }

  D("options: %p\n", options);
  return true;
}
