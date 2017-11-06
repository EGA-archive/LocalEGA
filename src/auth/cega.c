#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <errno.h>
#include <stdbool.h>
#include <libpq-fe.h>

#include <curl/curl.h>
#include <jq.h>

#include "debug.h"
#include "config.h"
#include "backend.h"

#define URL_SIZE 1024

struct curl_res_s {
  char *body;
  size_t size;
};

/* callback for curl fetch */
size_t
curl_callback (void *contents, size_t size, size_t nmemb, void *p) {
  const size_t realsize = size * nmemb;                      /* calculate buffer size */
  struct curl_res_s *cres = (struct curl_res_s *) p;   /* cast pointer to fetch struct */

  /* expand buffer */
  cres->body = (char *) realloc(cres->body, cres->size + realsize + 1);

  /* check buffer */
  if (cres->body == NULL) {
    D("ERROR: Failed to expand buffer in curl_callback\n");
    /* free(p); */
    return -1;
  }

  /* copy contents to buffer */
  memcpy(&(cres->body[cres->size]), contents, realsize);
  cres->size += realsize;
  cres->body[cres->size] = '\0';

  return realsize;
}

static const char*
get_from_json(jq_state *jq, const char* query, jv json){
  
  const char* res = NULL;

  D("Processing query: %s\n", query);

  if (!jq_compile(jq, query)){ D("Invalid query"); return NULL; }

  jq_start(jq, json, 0); // no flags
  jv result = jq_next(jq);
  if(jv_is_valid(result)){

    if (jv_get_kind(result) == JV_KIND_STRING) {
      res = jv_string_value(result);
      D("Valid result: %s\n", res);
      jv_free(result);
    } else {
      D("Valid result but not a string\n");
      //jv_dump(result, 0);
      jv_free(result);
    }
  }
  return res;
}

bool
fetch_from_cega(const char *username, char **buffer, size_t *buflen, int *errnop)
{
  CURL *curl;
  CURLcode res;
  bool success = false;
  char endpoint[URL_SIZE];
  struct curl_res_s *cres = NULL;
  char* endpoint_creds = NULL;
  jv parsed_response;
  jq_state* jq = NULL;
  const char *pwd = NULL;
  const char *pbk = NULL;

  D("Contacting cega for user: %s\n", username);

  if(!options->rest_user || !options->rest_password){
    D("Empty CEGA credentials\n");
    return false; /* early quit */
  }

  curl_global_init(CURL_GLOBAL_DEFAULT);
  curl = curl_easy_init();

  if(!curl) { D("libcurl init failed\n"); goto BAIL_OUT; }

  if( !sprintf(endpoint, options->rest_endpoint, username )){
    D("Endpoint URL looks weird for user %s: %s\n", username, options->rest_endpoint);
    goto BAIL_OUT;
  }

  cres = (struct curl_res_s*)malloc(sizeof(struct curl_res_s));
  
  curl_easy_setopt(curl, CURLOPT_NOPROGRESS    , 1L               ); /* shut off the progress meter */
  curl_easy_setopt(curl, CURLOPT_URL           , endpoint         );
  curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION , curl_callback    );
  curl_easy_setopt(curl, CURLOPT_WRITEDATA     , (void *)cres     );
  curl_easy_setopt(curl, CURLOPT_FAILONERROR   , 1L               ); /* when not 200 */

  curl_easy_setopt(curl, CURLOPT_HTTPAUTH      , CURLAUTH_BASIC);
  endpoint_creds = (char*)malloc(1 + strlen(options->rest_user) + strlen(options->rest_password));
  sprintf(endpoint_creds, "%s:%s", options->rest_user, options->rest_password);
  D("CEGA credentials: %s\n", endpoint_creds);
  curl_easy_setopt(curl, CURLOPT_USERPWD       , endpoint_creds);
 
  /* curl_easy_setopt(curl, CURLOPT_SSLCERT      , options->ssl_cert); */
  /* curl_easy_setopt(curl, CURLOPT_SSLCERTTYPE  , "PEM"            ); */

#ifdef DEBUG
  curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 0L);
  curl_easy_setopt(curl, CURLOPT_SSL_VERIFYHOST, 0L);
#endif

  /* Perform the request, res will get the return code */
  D("Connecting to %s\n", endpoint);
  res = curl_easy_perform(curl);
  D("CEGA Request done\n");
  if(res != CURLE_OK){
    D("curl_easy_perform() failed: %s\n", curl_easy_strerror(res));
    goto BAIL_OUT;
  }

  D("Parsing the JSON response\n");
  parsed_response = jv_parse(cres->body);

  if (!jv_is_valid(parsed_response)) {
    D("Invalid response\n");
    goto BAIL_OUT;
  }

  /* Preparing the queries */
  jq = jq_init();
  if (jq == NULL) { D("jq error with malloc"); goto BAIL_OUT; }

  pwd = get_from_json(jq, options->rest_resp_passwd, jv_copy(parsed_response));
  pbk = get_from_json(jq, options->rest_resp_pubkey, jv_copy(parsed_response));

  /* Adding to the database */
  success = add_to_db(username, pwd, pbk);

BAIL_OUT:
  D("User %s%s found\n", username, (success)?"":" not");
  if(cres) free(cres);
  if(endpoint_creds) free(endpoint_creds);

  jv_free(parsed_response);
  jq_teardown(&jq);

  curl_easy_cleanup(curl);
  curl_global_cleanup();
  return success;
}
