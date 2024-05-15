add_tag.py V8.0.0
=================

Add tags in address and subject headers, text and HTML bodies and calendar objects.

## Parameters
* address_tag (string): address tag for from, sender, to and cc headers (empty for disabling address tagging)
* internal_list (string): name of address list with internal domains which are excluded from address tagging of to/cc headers (empty for disabling to/cc header address tagging)
* subject_tag (string): tag for subject header (empty for disabling subject tagging)
* text_tag (string): name of annotation for tagging text body (empty for disabling text body tagging)
* text_top (boolean): insert text tag at top else at the bottom
* html_tag (string): name of annotation for tagging HTML body (empty for disabling HTML body tagging)
* html_top (boolean): insert HTML tag at top else at the bottom
* html_id (string): ID of HTML tag
* calendar_tag (string): calendar tag for organizer field (empty for disabling calendar tagging)

## URL lists
* Internal domains: list of internal domains

## Hold Areas
* Add tag: mails with errors
