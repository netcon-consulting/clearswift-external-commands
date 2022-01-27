rewrite_url.py V2.0.2
=====================

Rewrite URLs in text and html body by resolving redirects and replacing URL parts.

## Parameters
* redirect_list (string): name of URL list with redirector domains (empty for disabling resolving redirects)
* timeout (integer): timeout for resolving redirects in seconds
* substitution_list (string): name of lexical expression list with URL substitutions (empty for disabling replacing URL parts)
* annotation_text (string): name of annotation applied to modified text body (empty for disabling annotating text body)
* annotation_html (string): name of annotation applied to modified html body (empty for disabling annotating html body)

## URL lists
* Redirector domains: list of redirector domains

## Lexical expression lists
* URL substitutions: list of URL substitutions (regex and replacement separated by newline)

## Hold Areas
* Rewrite URL: mails with errors
