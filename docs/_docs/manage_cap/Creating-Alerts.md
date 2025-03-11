# Creating CAP Alerts

To create a CAP Alert access the CAP composing interface from the explorer menu as below and add a new cap alert page:

![CAP Explorer](../../_static/images/cap/cap_explorer.png "CAP Explorer")

------------------------------------------------------------------------

## Sections in the Alert Page and corresponding XML

The overall Document Object Model of an alert is as below:

![Alert DOM](../../_static/images/cap/dom.jpg "CAP Document Object Model")

### Alert Identification

It contains the following entities required for a valid CAP message:

- Sender ID(sender),
- Sent Dat/Time (sent),
- Message Status (status),
- Message Type (msgType),
- Scope(scope),
- Restriction (restriction),
- Addresses (addresses),
- Note (note),
- Reference IDs (references) and
- Incident ids (incidents).

The alert identifier is generated automatically and is not editable.

```{note}
Some fields are visible based on selection of different parameters.
```

![Alert Identification](../../_static/images/cap/alert_identification.png "Alert Identification section")

### Alert Information

Corresponds to the `<info>` element in the CAP message. The <info> entity specifies the alert's details. At least
one <info> block is required for an alert. If you support multiple languages, it is recommended that you use one <info>
block for each language for the same <alert> entity.:

A CAP message expects at least one `<info>` element to be present. Multiple `<info>` blocks should all have the
same `<category>` and `<event>` element values.

Each `Information` block contains the following elements:

- Langauge (langauge
- Event Category/Categories (category)
- Event Type (event)
- Response Type/Types (responseType)
- Urgency (urgency)
- Severity (severity)
- Certainty (certainty)
- Audience (audience)
- Event Code/Codes (eventCode)
- Effective Date/Time (effective)
- Onset Date/Time (onset)
- Expiration Date/Time (expires)
- Sender Name (senderName)
- Headline(headline)
- Event description (description)
- Instructions (instruction)
- Information URL (web),
- Contact Info (contact) and
- Parameter/Parameters(parameter)

![Alert Info](../../_static/images/cap/alert_info.png "Alert Info")

#### Alert Area

Information Entity that defines the geographic area to be notified. Multiple areas can be defined in the alert. Each
area contains the following elements:

- Area Description (areaDesc),
- Area Polygon/Polygons (polygon),
- Area Circle/Circles (circle),
- Area Geocode/Geocodes (geocode),
- Altitude (altitude),
- Ceiling (ceiling)

![Alert Area](../../_static/images/cap/alert_area_options.png "Alert Area section")

The Alert area input has 4 selector options:

- Admin Boundary (area is picked from predefined boundaries). To use this option, ensure that admin boundaries are
  initially loaded. Refer to [Setting up boundaries](./Setting-Boundaries.md) section.

![Alert Area boundary](../../_static/images/cap/alert_area_boundary.png "Alert Area section")

- Polygon (drawing a polygon). If you have not yet uploaded boundaries refer to [Setting boundaries Section](./Setting-Boundaries.md#setting-boundaries)

![Alert Area polygon](../../_static/images/cap/alert_area_polygon.png "Alert Area section")

- Circle (drawing a circle which specifies the latitude, longitude and radius)

![Alert Area circle](../../_static/images/cap/alert_area_circle.png "Alert Area section")

- Geocode (specifying area geocode name and value). Using this option presumes knowleged of the coding system

![Alert Area geocode](../../_static/images/cap/alert_area_geocode.png "Alert Area section")

#### Alert Resource

Entity that defines supplemental information related to an <info> object Multiple instances of this section are allowed.
It contains:

- Description (resourceDesc), MIME Type (mimeType), File Size (size), URI (uri), Dereferenced URI (derefUri) and
  Digest (digest)**

The Alert resource input has 2 selector options:

- File resource (takes in a file and description)

![Alert Resource](../../_static/images/cap/alert_resource_file.png "Alert Resource section")

- External resource

![Alert Resource](../../_static/images/cap/alert_resource_external.png "Alert Resource section")

#### Additional CAP Inputs

Addition alert information elements include parameters and event codes

### Incidents

This defines the reference incident to the current alert, if any.

![Alert Incidents](../../_static/images/cap/alert_incidents.png "Alert Incidents section")

---