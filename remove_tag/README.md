remove_tag.py V2.0.0
====================

Remove tags in address and subject headers, text and html bodies and calendar objects.

## Parameters
* address_tag (string): address tag for from, to and cc headers
* clean_text (boolean): on removal also clean address tag from text body
* clean_html (boolean): on removal also clean address tag from html body
* subject_tag (string): tag for subject
* text_tag (string): tag for text body
* html_tag (string): tag for html body
* html_tag_id (string): ID of html tag
* calendar_tag (string): calendar tag for organizer field

## Address lists
* Internal domains: list of internal domains

## Hold Areas
* Remove tag: mails with errors
