# City Forecasts

City forecasts on the homepage and forecasts page can be added in three ways:

1. Manually adding daily forecasts
2. Uploading a CSV file prepared offline
3. Fetching city forecasts automatically from an external source

For step-by-step instructions on CSV uploads, see [Uploading a CSV forecast](#uploading-a-csv-forecast-manually).

> **Note:** The forecast manager comes with predefined weather conditions and icons. See the Yr weather symbols documentation for icons and naming conventions: <https://api.met.no/weatherapi/weathericon/2.0/documentation>

## Before you start

You need a ClimWeb admin account with staff access. Go to your site's admin URL (for example, `https://your-nmhs-site.org/cms-admin/`) and sign in with your credentials. Your system administrator should have given you this URL when your account was created. If you do not have it, ask them. It typically ends in `/cms-admin/` or `/admin/`. If you do not have an account, contact your system administrator.

For the CSV upload method, you also need a spreadsheet application such as Microsoft Excel or LibreOffice Calc.

## Manually adding forecasts

The **City Forecast** menu in the left sidebar has five items: Cities, Daily Weather, Add Forecasts, Load Forecasts, and Settings.

![City Forecast menu in the left sidebar, expanded to show five items: Cities, Daily Weather, Add Forecasts, Load Forecasts, and Settings](../_static/images/city_forecasts/forecast_explorer.png "City Forecast menu")

You can:
- Add/Edit/Delete a city (city name and location).

    ![Add City form showing City Name set to Gondar, coordinates filled in as 12.60417, 37.46833, and a map pin placed over northern Ethiopia](../_static/images/city_forecasts/add_city.png "Add City form with geocoded location")

- Import city forecasts in CSV format.

    ![City Forecast menu with Add Forecasts highlighted, showing the Forecast Manager page with a CSV upload area and an empty data grid](../_static/images/city_forecasts/add_forecast_explorer.png "City Forecast menu: Add Forecasts selected")


    Import city forecasts from a CSV file or type values into the data grid. To enter data manually, click any cell in the grid and type the value. When you are finished entering data, fill in the **Forecasts Date** and **Effective period** fields and click **Save**. For step-by-step CSV upload instructions, see [Uploading a CSV forecast](#uploading-a-csv-forecast-manually).

    ![Add Forecast page with a CSV file selected, Forecasts Date set to 2023-07-10, Match Fields dropdowns for City, Min Temp, Max Temp, and Condition, and a data grid showing three sample cities](../_static/images/city_forecasts/add_forecast.png "Add Forecast page with CSV uploaded and fields matched")

- Preview previously added city forecasts (last 7 days).

    ![City Forecast menu with Load Forecasts highlighted, showing a forecast data table and weather map of East Africa side by side](../_static/images/city_forecasts/load_forecast_explorer.png "City Forecast menu: Load Forecasts selected")

    Switch between available dates and view data in either table or map format.

    ![Load Forecasts page showing a date selector set to July 19, 2023, a table of 17 cities with Min Temp, Max Temp, and Condition columns, and a weather icon map of East Africa](../_static/images/city_forecasts/load_forecast.png "Load Forecasts: date selector, data table, and weather map")

- Add a daily weather summary.

    ![City Forecast menu with Daily Weather highlighted, showing the Daily Weathers list with one entry and an Add daily weather button](../_static/images/city_forecasts/daily_weather_explorer.png "City Forecast menu: Daily Weather selected")

    ![New Daily Weather form with three sections: Weather Summary with a date field and rich text editor, Weather Forecast with a date field and rich text editor, and Extremes with a date field](../_static/images/city_forecasts/daily_weather.png "New Daily Weather form")

    The daily weather summary form has three sections:

    - **Weather Summary**: set the summary date and describe observed conditions using the rich text editor.
    - **Weather Forecast**: set the forecast date and describe expected conditions.
    - **Extremes**: add records of extreme station readings from the previous day (for example, the hottest or coldest station). Each entry requires a title, location name, and numeric value.

    Here is how it appears on the website:

    ![Public Daily Weather Report page showing a Stations with Extreme Measurements section listing the hottest and coldest stations, a Forecast Summary paragraph, and a Past Weather Summary paragraph](../_static/images/city_forecasts/daily_weather_preview.png "Daily Weather Report as it appears on the public website")


## Uploading a CSV forecast manually

Prepare forecast data offline in a spreadsheet, then upload it here.

> **Note:** You must be logged in to the ClimWeb admin before following these steps. Go to your site's admin URL (for example, `https://your-nmhs-site.org/cms-admin/`) and sign in with your credentials.

If you are setting up ClimWeb for the first time and have not added any cities or configured forecast parameters, start at Step 1. If your instance already has cities, parameters, and at least one forecast period configured, jump straight to [Step 3](#step-3-download-the-csv-template). If you are not sure, start at Step 1.

### Step 1: Configure forecast setting

Forecast settings control three things: what time periods you can forecast for, what data columns appear in your CSV template, and what weather condition icons are available.

Go to **Settings → Forecast setting** in the left sidebar.

![Forecast setting page showing the Forecast Periods tab with one period configured: Day at 12:00](../_static/images/city_forecasts/csv_upload/01_forecast_settings_periods.png "Forecast setting: Forecast Periods tab")

#### Forecast Periods

Click **+ Add Forecast Period**. Set the **Forecast Effective Time** to `12:00` and the **Label** to `Day`. If your service publishes morning and afternoon forecasts separately, you can add a second period here; otherwise one is enough.

Click **Save**.

#### Forecast Data Parameters

Click the **Forecast Data Parameters** tab. Each parameter you add here becomes a column in your CSV template.

Click **+ Add Data Parameter** for each of the following parameters. Leave **Use predefined parameters** ticked. Set **Parameter Type** to `Number` for all four.

| Parameter Label | Parameter | Parameter Type | Unit of measurement |
|---|---|---|---|
| Max Temperature | Maximum Air Temperature | Number | °C |
| Min Temperature | Minimum Air Temperature | Number | °C |
| Wind Speed | Wind Speed | Number | m/s |
| Relative Humidity | Relative Humidity | Number | % |

![Forecast Data Parameters tab showing all four parameters configured: Max Temperature, Min Temperature, Wind Speed, and Relative Humidity, each with Parameter Type set to Number](../_static/images/city_forecasts/csv_upload/02_forecast_data_parameters.png "Forecast setting: Forecast Data Parameters tab")

Click **Save**.

#### Forecast Weather Conditions

Click the **Forecast Weather Conditions** tab. Conditions are the weather icons that appear on the forecast map. The label you give each condition becomes the value in your CSV's Condition column, so spelling and capitalisation must match exactly. In some documentation this is called a condition code.

Click **+ Add Weather Condition**. For the **Weather Symbol** field, click the button to open the **Choose symbol** dialog.

![Weather symbol picker showing a grid of icons including Clear sky Day, Partly Cloudy Day, Rain, and Heavy Rain](../_static/images/city_forecasts/csv_upload/04_symbol_picker.png "Weather symbol picker")

Click an icon. Add these four conditions.

| Symbol to select | Label |
|---|---|
| Clear sky Day | Clear Sky |
| Partly Cloudy Day | Partly Cloudy |
| Rain | Rain |
| Heavy Rain | Heavy Rain |

![Forecast Weather Conditions tab showing all four conditions: Clear Sky, Partly Cloudy, Rain, and Heavy Rain, each with a weather icon selected](../_static/images/city_forecasts/csv_upload/03_weather_conditions.png "Forecast setting: Forecast Weather Conditions tab")

Click **Save**.

> **Note:** **Forecast Source** and **Other Settings** are for the automated Yr.no integration. Skip them for CSV uploads.

### Step 2: Add cities

In the left sidebar, go to **City Forecast → Cities**, then click **Add City**.

Type a city name in the **City Name** field. ClimWeb uses OpenStreetMap to look up the location and place a pin on the map automatically.

![Add City page showing "Dar es Salaam" entered in the name field, with coordinates filled in automatically and a map pin placed over the coast of Tanzania](../_static/images/city_forecasts/csv_upload/05_add_city.png "Add City: location geocoded automatically from the city name")

Check that the pin landed in the right place, then click **Save**. Repeat for every city you want to include.

If the pin is in the wrong location, drag it to the correct spot, or type the correct coordinates directly into the **Latitude** and **Longitude** fields. If ClimWeb cannot find the city by name, try adding the country (for example, `Nairobi, Kenya` instead of `Nairobi`).

### Step 3: Download the CSV template

In the left sidebar, go to **City Forecast → Add Forecasts**, then click **+ Add Forecast**. The page that opens is headed **New**: this is where you enter and upload your forecast data.

Click **download a template** in the blue notice at the top of the page to download `forecast_template.csv`.

![Add Forecast page showing the blue information banner with the "download a template" link, the Forecasts Date field, Effective period dropdown, and the empty data grid on the right](../_static/images/city_forecasts/csv_upload/06_add_forecast_empty.png "Add Forecast page: download the template from the blue banner")

The template reflects the cities and parameters currently in the system. If you add cities after downloading, re-download the template or add rows manually.

> **Note:** The date is not a column in the CSV. You set the forecast date separately in Step 6 after uploading the file.

```
City,Max Temperature,Min Temperature,Wind Speed,Relative Humidity,Condition
Nairobi,,,,,
Mombasa,,,,,
Kisumu,,,,,
```

| Column | What to enter |
|---|---|
| City | Exact city name as added in Step 2 |
| Max Temperature | Number in °C, no units |
| Min Temperature | Number in °C, no units |
| Wind Speed | Number in m/s, no units |
| Relative Humidity | Number in %, no units |
| Condition | Exact label from Step 1 (for example, `Clear Sky`) |

### Step 4: Fill in your forecast data

Open the template in a spreadsheet or text editor and enter values for each city:

- **Condition values must match exactly.** Type `Clear Sky`, `Rain`, or whichever label you set up in Step 1. ClimWeb rejects the upload if any condition label does not match.
- **City names must match exactly.** The names in your CSV must be spelled the same way as when you added the cities in Step 2, including capitalisation. ClimWeb skips rows with city names it does not recognise.
- **All cells must have a value.** Every cell needs a value or the upload will fail.
- **Data column values must be numbers.** Temperature, wind speed, and humidity must be numbers. Negative values are accepted (for example, a minimum temperature of `-3`). Do not include units such as °C or m/s in the cells.

```
City,Max Temperature,Min Temperature,Wind Speed,Relative Humidity,Condition
Eldoret,26,14,3,65,Partly Cloudy
Kisumu,31,18,4,72,Rain
Mombasa,33,24,6,80,Clear Sky
Nairobi,28,15,3,60,Partly Cloudy
Nakuru,27,13,2,58,Clear Sky
```

![Filled forecast_template.csv open in Excel showing five Kenyan cities with Max Temperature, Min Temperature, Wind Speed, Relative Humidity, and Condition values entered](../_static/images/city_forecasts/csv_upload/03b_filled_csv_excel.png "Filled CSV template open in Excel")

Save the file. In Excel, use **File → Save As** and select **CSV UTF-8 (Comma delimited)** from the format dropdown. Saving as a different CSV format may cause the upload to fail. One city per upload is valid, but three or more makes column-matching errors easier to spot.

### Step 5: Upload the CSV and verify column matching

Go back to the **Add Forecast** page. Click **Choose File** and select your filled CSV.

A **Match Fields** section appears above the data grid, showing one dropdown per column. ClimWeb matches each CSV column to the corresponding parameter by comparing your column headers to the parameter names from Step 1.

Check each dropdown. If a column is wrong, open its dropdown and select the right parameter. Pay particular attention to the **City** column: if it is not correctly mapped, no rows will appear in the data grid. ClimWeb ignores any extra columns that do not match a parameter.

![Add Forecast page after uploading the CSV, showing the Match Fields dropdowns: City, Max Temperature, Min Temperature, Wind Speed, Relative Humidity, Condition, all correctly matched, with the data grid below showing five city rows](../_static/images/city_forecasts/csv_upload/07_match_fields.png "Match Fields section: verify each column is mapped correctly before saving")

### Step 6: Set the date and save

On the left side of the page, fill in the remaining fields:

1. **Forecasts Date**: enter the date this forecast covers in `YYYY-MM-DD` format, for example `2026-05-26`.
2. **Effective period**: select the period you set up earlier, for example `Day`. If the dropdown is empty, go to **Settings → Forecast setting → Forecast Periods** and add at least one period first.
3. **Replace existing data if found**: this checkbox is ticked by default. Leave it ticked to permanently replace the existing forecast with your new data. Untick it to keep the existing forecast and discard your new upload. **Overwriting cannot be reversed; the previous data is deleted.**

![Add Forecast page with Forecasts Date set to 2026-05-26, Effective period set to Day, and the data grid showing all five city rows](../_static/images/city_forecasts/csv_upload/08_date_period_filled.png "Add Forecast: date and period set, ready to save")

Click **Save**. ClimWeb publishes the forecast immediately and takes you back to the Forecasts list. There is no separate publish step. To confirm, go to your site's homepage (for example, `https://your-nmhs-site.org/`), click **Forecasts** in the navigation, and check that the forecast appears.

![Forecasts list showing one saved entry: 2026-05-26, Day period, updated 2 hours ago](../_static/images/city_forecasts/csv_upload/09_forecast_list.png "Forecasts list after saving")

Click the forecast row to review the data.

To correct a forecast, upload a new CSV for the same date and period with **Replace existing data if found** ticked. To delete a forecast, open it from the Forecasts list and click **Delete** at the bottom of the page.

![Forecast detail view showing five Kenyan cities: Eldoret, Kisumu, Mombasa, Nairobi, Nakuru, each with a weather condition icon and values for Max Temperature, Min Temperature, Wind Speed, and Relative Humidity](../_static/images/city_forecasts/csv_upload/10_forecast_view.png "Forecast detail: Tuesday 26 May, Day period")

> **If something goes wrong:**
>
> - **Data grid is empty after upload:** You may have saved it in a non-CSV format, or Excel may still have it open. Close it in Excel, save it again as CSV with UTF-8 encoding (select this option in the **Save As** dialog), and try again.
> - **Fewer rows than expected in the data grid:** City names in your CSV do not match the names in the system. ClimWeb skips any city names it does not recognise, without showing a warning. Download a fresh template and compare the city names.
> - **Error when saving:** Confirm that **Forecasts Date** and **Effective period** are both filled in. Both are required.
> - **Columns matched to the wrong parameters:** Correct the **Match Fields** dropdowns before saving. If you have already saved with wrong mappings, upload again with **Replace existing data if found** ticked and the dropdowns set correctly.
> - **Some rows show blank values in the data grid:** A cell in your CSV was left empty. Fill in every cell, save the file, and upload again.

## Fetching from an external source

ClimWeb automatically fetches forecasts — temperature, wind speed, and weather conditions — from Yr.no (a free global forecast service) and publishes them for all your cities. ClimWeb uses each city's map location (set in [Step 2](#step-2-add-cities)) to request the data. At least one city must have a map location set before automated fetching will work — any city you add later is included on the next scheduled fetch, as long as it has a map location.

To enable automated fetching, go to **Settings → Forecast setting** and open the **Forecast Source** tab. Tick **Enable automated forecasts** and click **Save**. No other settings are needed. Disabling this setting stops new fetches — but any forecasts already published remain visible. Re-enabling resumes fetches; gaps are not backfilled.

![Forecast Source tab showing the Enable automated forecasts checkbox, which is checked](../_static/images/city_forecasts/autoforecast.png "Forecast setting: Forecast Source tab")

The first fetch runs **within 60 minutes**. After that, forecasts update **every hour** and retrieve up to **7 calendar days** of data per city.

Automated fetches cover the standard forecast variables — temperature, wind, pressure, and precipitation — but ClimWeb does not store relative humidity from the Yr.no data. To include humidity values, enter them manually or via the [CSV upload method](#uploading-a-csv-forecast-manually).

If Yr.no returns a weather condition not listed in the **Forecast Weather Conditions** tab, ClimWeb adds it and assigns a default icon.

ClimWeb also creates **Forecast Periods** automatically — no advance setup is required. Yr.no provides hourly data, so ClimWeb creates one forecast period for each hour in the **Forecast Periods** tab — for example, `9:00` and `14:00` — alongside any existing periods, such as `Day`.

You can use both Yr.no automated forecasts and CSV uploads at the same time. Because they use different forecast periods, **they do not overwrite each other**.

The first fetch adds entries in bulk: one forecast per hour for approximately the first 48 hours, then one every six hours, plus any new periods and weather conditions.

> **Note:** This bulk addition of entries is expected. Leave these forecast entries in place — ClimWeb uses all of them.

**To verify:** Go to **City Forecast → Load Forecasts** and confirm new entries have appeared. ClimWeb does not automatically remove forecasts older than 7 days. You can delete them from **City Forecast → Load Forecasts** without affecting current or future fetches.

**If automated forecasts are not updating:**

| Problem | Likely cause | What to do |
|---|---|---|
| Forecasts stopped updating | The automated forecasts setting was turned off, or a scheduled task on the server stopped running | Confirm **Enable automated forecasts** is still ticked in **Settings → Forecast setting** (open the **Forecast Source** tab). If it is ticked and forecasts are still not updating, ask your system administrator to verify that the Celery beat scheduler (a background process that runs scheduled tasks on the server) is running and that the hourly forecast fetch task has not failed. |
| No forecast data appears after setup (check site address) | The site's web address is still set to the temporary default `localhost` instead of your real site address | Ask your system administrator to check **Settings → Sites** and set the site's web address to your real site address (most common when ClimWeb has just been set up for the first time). If the site address is still set to `localhost`, ClimWeb cannot correctly generate the internal URLs it needs to process fetched data. |
| No forecast data appears after setup (check network access) | Server cannot reach the Yr.no API | Ask your system administrator to confirm that outbound HTTPS connections to `api.met.no` are not blocked by a firewall or proxy (that is, the server is allowed to make requests to external websites). |
| Data is not up to date | Updates happen once per hour | Wait up to 60 minutes. If still not updated, confirm the **Enable automated forecasts** checkbox is still ticked. If it is ticked and data is still not updating, ask your system administrator to verify that the Celery beat scheduler (a background process that runs scheduled tasks on the server) is running. |
| Some cities show no forecast | The city has no location set | Go to **City Forecast → Cities** and confirm the city has a map location set (see Step 2). |
| Forecast data has gaps after a connection outage | Fetches were skipped during the outage | No action needed. Published forecasts remain visible. Fetches resume automatically once the connection is restored. |
| A city shows a wrong or missing condition icon | ClimWeb created a new weather condition automatically and used a default icon | Go to **Settings → Forecast setting** and open the **Forecast Weather Conditions** tab. Find the condition with the default or missing icon and assign the correct icon. |

Once forecasts appear in **City Forecast → Load Forecasts**, no further action is needed.
