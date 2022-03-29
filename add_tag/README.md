add_tag.py V4.0.0
=================

Add tags in address and subject headers, text and html bodies and calendar objects.

## Parameters
* address_tag (string): address tag for from, to and cc headers (empty for disabling address tagging)
* internal_list (string): name of address list with internal domains which are excluded from address tagging of to/cc headers (empty for disabling to/cc header address tagging)
* subject_tag (string): tag for subject header (empty for disabling subject tagging)
* text_tag (string): name of annotation for tagging text body (empty for disabling text body tagging)
* text_top (boolean): insert text tag at top else at the bottom
* html_tag (string): name of annotation for tagging html body (empty for disabling html body tagging)
* html_top (boolean): insert html tag at top else at the bottom
* html_id (string): ID of html tag
* calendar_tag (string): calendar tag for organizer field (empty for disabling calendar tagging)

## Address lists
* Internal domains: list of internal domains

## Hold Areas
* Add tag: mails with errors
