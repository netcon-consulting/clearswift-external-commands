remove_tag.py V5.0.0
====================

Remove tags in address and subject headers, text and html bodies and calendar objects.

## Parameters
* address_tag (string): address tag for from, to and cc headers (empty for disabling address untagging)
* clean_text (boolean): clean text body on address tag removal
* clean_html (boolean): clean html body on address tag removal
* subject_tag (string): tag for subject header (empty for disabling subject untagging)
* text_tag (string): name of annotation for tagging text body (empty for disabling text body untagging)
* html_id (string): ID of html tag (empty for disabling html body untagging)
* calendar_tag (string): calendar tag for organizer field (empty for disabling calendar untagging)

## Address lists
* Internal domains: list of internal domains

## Hold Areas
* Remove tag: mails with errors
