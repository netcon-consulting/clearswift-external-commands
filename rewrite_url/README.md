rewrite_url.py V1.0.0
=====================

Rewrite URLs in text and html body by resolving redirects and replacing URL parts.

## Parameters
* redirect_list (string): name of URL list with redirector domains
* timeout (integer): timeout for resolving redirects in seconds
* substitution_list (string): name of lexical expression list with URL substitutions

## URL lists
* Redirector domains: list of redirector domains

## Lexical expression lists
* URL substitutions: list of URL substitutions (regex and replacement separated by newline)

## Hold Areas
* Rewrite URL: mails with errors
