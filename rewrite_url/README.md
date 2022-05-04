rewrite_url.py V6.0.0
=====================

Rewrite URLs in text and html body by resolving redirects (and optionally check if resolved URL is blacklisted) and replacing URL parts.

## Parameters
* exception_list (string): name of URL list with URLs that will not be rewritten (empty for disabling rewrite exceptions)
* redirect_list (string): name of URL list with redirector domains (empty for disabling resolving redirects)
* timeout (integer): timeout for resolving redirects in seconds
* check_redirect (boolean): check if resolved redirect URLs are blacklisted
* url_blacklist (string): name of URL blacklist (empty for no custom blacklist)
* url_whitelist (string): name of URL whitelist (empty for no custom whitelist)
* substitution_list (string): name of lexical expression list with URL substitutions (empty for disabling replacing URL parts)
* token_list (string): name of lexical expression list with substitution tokens (empty for disabling substitution tokens)
* annotation_text (string): name of annotation applied to modified text body (empty for disabling annotating text body)
* annotation_html (string): name of annotation applied to modified html body (empty for disabling annotating html body)

## URL lists
* Redirector domains: list of redirector domains
* URL blacklist: URL blacklist
* URL whitelist: URL whitelist

## Lexical expression lists
* URL substitutions: list of URL substitutions (regex and replacement separated by newline)
* Substitution tokens: list of substitution tokens

## Hold Areas
* Rewrite URL: mails with errors
