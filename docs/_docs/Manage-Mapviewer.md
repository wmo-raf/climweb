# Mapviewer

The MapViewer is the interactive map of your ClimWeb website. It brings together the spatial data published by your National Meteorological and Hydrological Service (NMHS), such as forecasts, observations, satellite products, climate indices and warnings, and lets anyone explore them, combine them and analyse them over an area of interest.

The MapViewer is available at the `/mapviewer/` address of your ClimWeb website (for example `https://www.meteo.gov.gh/mapviewer/`).

```{note}
The ClimWeb MapViewer is derived from the open-source map of [Global Nature Watch](https://globalnaturewatch.org/) (formerly Global Forest Watch). If you have used their map before, you will find the same logic here: browse data by theme, switch layers on and off, adjust them from the legend and analyse them on the map.
```

The screenshots in this guide come from the MapViewer of the Ghana Meteorological Agency. The logo, themes and data layers you see on your own MapViewer depend on how it has been configured by your administrators.

---

## Overview

![MapViewer overview](../_static/images/mapviewer/mapviewer_overview.png "MapViewer overview")

**1. Organisation logo**: shows who publishes the map and takes you back to the organisation website.

**2. Search bar**: finds a place, goes to coordinates or looks up a dataset by name.

**3. Log in**: gives access to your account and to data reserved for registered users.

**4. Themes**: the available data is organised into themes, such as Precipitation, Temperature or Wind. Click a theme to browse its data.

**5. Data panel**: lists the sub-themes and data layers of the selected theme. Use the toggles to display layers on the map.

**6. Legend and analysis**: lists the layers displayed on the map with their legend and settings. The **Analysis** tab lets you analyse the data over an area.

**7. Map controls**: zoom in and out, show the map only, share or embed the current view, change the map settings, reload or print the map, and open the MapViewer how-to guide.

---

## The header

The header runs along the top of the MapViewer and stays visible at all times.

### Organisation logo

The logo of your organisation is displayed in the top-left corner of the header. Click it to leave the map and go to the page chosen by your administrators, usually the home page of the organisation website.

Depending on the configuration, a few navigation links can also be displayed next to the logo.

> Administrators set the logo, the page it links to and the navigation links in the **Geomanager Settings**, under the **Navigation Settings** tab.

### Logging in

You don't need an account to use the MapViewer: all public data can be viewed without logging in. Logging in gives access to:

- data layers that your organisation has reserved for registered users,
- your **Areas of Interest (AOI)**: areas you have saved to analyse them again later.

To log in, click **Log In** in the top-right corner of the header. A login window opens:

![Log in window](../_static/images/mapviewer/mapviewer_login.png "Log in window")

**1. Log In button**: opens or closes the login window.

**2. Email and password**: enter the email address and password of your account, then click **LOGIN**.

**3. Forgot password**: enter your email address to receive instructions to reset your password.

**4. Sign up**: create a new account. A confirmation email is sent to activate it.

Once you are logged in, the **Log In** button is replaced by your name and avatar. Click them to open your account menu, where you can view your profile, find your saved Areas of Interest and log out.

```{note}
The login button is only displayed if your administrators have enabled user accounts, and the **Sign up** link only if they allow visitors to create their own account. Both options are available in the **Geomanager Settings**, under the **My Account Settings** tab.
```

---

## Browse and select data

All the data available in the MapViewer is organised in three levels:

- **Themes**: the main families of data, displayed as icons on the left of the map.
- **Sub-themes**: groups of related layers within a theme, for example *Forecast* and *Observation*.
- **Data layers**: the datasets themselves, which you can display on the map.

### Themes

The themes are listed in the vertical menu on the left side of the map. Each theme has an icon and a name. If there are more themes than can fit on your screen, scroll down the menu to see them all.

![Themes](../_static/images/mapviewer/mapviewer_themes.png "Themes")

**1. Selected theme**: click a theme to open the data panel and browse its sub-themes and data layers. The selected theme is highlighted.

**2. Number of active layers**: a blue badge on a theme icon shows how many of its layers are currently displayed on the map. This helps you find your active layers when you have combined data from several themes.

**3. Close the panel**: click the cross, or click the selected theme again, to close the data panel and free up space on the map. Closing the panel does not remove the layers from the map.

### Sub-themes

Within a theme, data layers are grouped into sub-themes. Each sub-theme has a header with its name that you can click to collapse or expand its list of layers.

![Sub-themes](../_static/images/mapviewer/mapviewer_subthemes.png "Sub-themes")

**1. Collapsed sub-theme**: click the header of a sub-theme to hide its layers. This is useful to quickly reach the other sub-themes when a theme contains many layers.

**2. Expanded sub-theme**: click the header again to show its layers.

**3. Number of active layers**: when a sub-theme is collapsed, a blue badge shows how many of its layers are displayed on the map.

Some sub-themes also display a set of options above their layers. Click an option to show the layers of the corresponding group.

### Data layers

Each data layer is presented with its name, its source and a set of tools.

![Data layer](../_static/images/mapviewer/mapviewer_layer.png "Data layer")

**1. Toggle**: switch the layer on to display it on the map, or off to remove it. You can also click the name of the layer. Once switched on, the layer is added to the legend, where you can adjust its settings.

**2. Name**: the title of the data layer.

**3. Source**: a short description of the layer, usually its data source or provider.

**4. Capabilities**: icons showing what you can do with the layer. Hover an icon to display its meaning:

- **Supports Time** (calendar icon): the layer has several dates or time steps. You can choose the date to display from the legend.
- **Supports Analysis**: the layer values can be analysed over an area from the **Analysis** tab.
- **Supports Clipping**: the layer can be clipped to an area.
- **Near Real Time**: the layer is updated frequently with recent data.

**5. Information**: click the **i** button to open the description of the layer.

The information window describes the data layer: what it shows, its resolution, geographic coverage, source and license, followed by an overview of the data. When available, the **LEARN MORE** button takes you to more information about the data.

![Data layer information](../_static/images/mapviewer/mapviewer_layer_info.png "Data layer information")

You can display several layers at the same time, from the same theme or from different themes. For example, you can combine a precipitation forecast with a temperature layer, or overlay observations on top of a forecast. The order and the transparency of the layers can then be adjusted from the legend.

### Filter layers

Some themes contain many data layers. To quickly find a layer, type a few words in the **Filter layers** field at the top of the data panel.

![Filter layers](../_static/images/mapviewer/mapviewer_filter.png "Filter layers")

**1. Filter field**: the list is filtered as you type, on the name and description of the layers. Click the cross, or press **Esc**, to clear the filter.

**2. Matching sub-themes**: only the sub-themes that contain matching layers are kept. In this example, all the layers matching *SPI* (Standardized Precipitation Index) belong to the *Observation* sub-theme.

The filter only applies to the selected theme. To search for data across all themes, use the search bar in the header.
