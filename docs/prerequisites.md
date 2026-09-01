# Prerequisites

## Tested platform

- Splunk Enterprise 10.4.1, build `5a009d941268`
- Splunk Python 3.13.11
- Classic Simple XML 1.1
- Modern browser supported by Splunk Enterprise 10.4

## Placement and permissions

Install on the search tier where users run the SPL. Users need permission to run the source search and the app-provided `aimarkdown` streaming command. Search permissions, quotas, risky-command controls, and role capabilities remain authoritative.

An administrator needs filesystem/service privileges to install the app, normalize ownership, and restart Splunk for first-time custom-command registration.

## Search contract

The source SPL must return one of:

- `ai_result_1`
- `ai_results_1`
- a field explicitly selected in the dashboard using the identifier grammar `^[A-Za-z][A-Za-z0-9_]{0,127}$`

The app appends `| aimarkdown` or `| aimarkdown field=<validated_field>` to the submitted search.

## Empty and error behavior

A search with no supported Markdown field returns a custom-command error or no renderable rows. An invalid explicit field is rejected before dispatch. Markdown larger than 200,000 characters per record is rejected.
