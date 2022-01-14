add_tag.py V1.0.1
=================

Add tags in address and subject headers, text and html bodies and calendar objects.

## Parameters
* address_tag (string): address tag for from, to and cc headers
* name_domain_list (string): name of address list with internal domains which are excluded from address tagging of to/cc headers; empty string disables to/cc header address tagging
* clean_text (boolean): on removal also clean address tag from text body
* clean_html (boolean): on removal also clean address tag from html body
* subject_tag (string): tag for subject
* text_tag (string): tag for text body
* text_top (boolean): insert text tag at top else at the bottom
* html_tag (string): tag for html body
* html_top (boolean): insert html tag at top else at the bottom
* html_tag_id (string): ID of html tag
* calendar_tag (string): calendar tag for organizer field

## Address lists
* Internal domains: list of internal domains

## Hold Areas
* Add tag: mails with invalid character encoding
