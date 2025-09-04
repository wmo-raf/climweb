# Atlas | Climweb Interactive Dashboards

![ClimWeb Atlas](../_static/images/atlas/atlas_showcase_notitle.png "ClimWeb Atlas")


The Atlas is a component of climweb that enables **modular, reusable, and CMS-editable dashboards** that bring together maps, charts, warming stripes, and narrative content for effective climate data storytelling. This component is **linked to the geomanager/mapviewer component** within climweb allowing linkage with already created datasets/layers and boundary data. It features:
- **Interactive dashboards** built using reusable blocks for maps, charts, text, images, and other components — enabling flexible and modular page layouts
- **Dynamic maps** supporting raster, vector tile, and WMS layers with custom symbology and legend options
- **Warming stripes** for a visual summary of long-term temperature trends
- **Customizable charts** for time-series and comparative analysis in bar, column, line or scatter plots
- A **user-friendly CMS** that allows teams to manage and update dashboard content independently
- Analysis at different **admin levels**

---


## Creating Dashboards

This section will guide you create and manage dashboards in an Atlas. 


### 1. Accessing Dashboards

1. Log in to the **Wagtail Admin**.
2. In the left menu, go to **Atlas → Dashboards**. If this is the first time creating the dashboards you will be prompted to first create a parent Atlas page that houses all dashboards. This will require a title and description.
3. Select an existing dashboard or click **Add Dashboard Page** to create a new one.

---

### 2. Creating a Dashboard Page

When creating a new Dashboard Page:

* Enter a **banner title** and optional **banner description**.
* Choose a **background color** (theme for the atlas) and **banner image** if desired.
* Add sections containing content using **blocks** (explained below). Each Section requires a section title and description.

---

### 3. Available Blocks in Dashboard Sections

You can build dashboards using different block types:

1. **Title & Text Block** – Simple block for adding a section heading and supporting text.
2. **Title, Text & Image Block** – A heading, text, and image side by side.
3. **Table Block** – Add tabular data (rows and columns).
4. **Map Block** – Display an interactive map (from a Map Snippet).
5. **Chart Block** – Display a chart (from a Chart Snippet).

---

### 4. Snippets

Snippets are reusable components for maps and charts. You must first create these before you can add them to a dashboard page.

#### 4.1 How to Create a Map Snippet

1. In Wagtail Admin, go to **Snippets → Dashboard Maps → Add Dashboard Map**.
2. Fill in the following:

   * **Name** – A short name for the map.
   * **Dataset** – Choose from datasets created in **GeoManager**.
   * **Layer Type** – One per snippet (**Raster**, **WMS**, or **Vector**).
   * **Legend** – Already defined in **GeoManager** when creating the dataset (not in the snippet).
   * **Admin Path** – Select an admin level and then click on the map to generate the path.
   * **Optional Description** – Explains what the map shows.
3. Save the snippet.

**Note:** Each snippet can only contain **one layer**.

---

#### 4.2 How to Create a Chart Snippet

1. In Wagtail Admin, go to **Snippets → Dashboard Charts → Add Chart**.
2. Fill in the following:

   * **Name** – A short name for the chart.
   * **Dataset** – Choose the dataset that will power the chart.
   * **Optional Description** – A short explanation of the chart.
   * **Chart Colour** - The color that will be applied to the graph when styling the data.
   * **Admin Path** – Select an admin level and then click on the map to generate the path.

3. Save the snippet.

---

### 5. Block Layout Rules

* Blocks can be arranged in any order.
* **When two Map blocks or two Chart blocks appear consecutively and each has a description**, the **text/title alternates sides automatically**:

  * Example: First block → text on the left, map/chart on the right.
  * Next block → text on the right, map/chart on the left.
* This ensures dashboards remain visually balanced and easy to read.

---

### 6. Publishing Your Dashboard

1. Once blocks are added, scroll to the bottom of the page.
2. Click **Save Draft** to preview or **Publish** to make the dashboard live.

---

✅ With this setup, you can create rich dashboards combining **text, images, tables, maps, and charts**—all styled for clarity and interactivity.


## Troubleshooting <a name="troubleshooting"></a>

### Common Issues
1. **Error Loading Data**:
   - Ensure you have a stable internet connection.
   - Check if the dataset or layer ID is valid.
2. **Selectors Not Updating**:
   - Refresh the page to reload parameter selectors.
   - Ensure the dataset supports the selected parameters.
3. **Date Range Not Applying**:
   - Verify that the selected date range has data available.

---

## 7. FAQs <a name="faqs"></a>

### Q: How do I reset a chart or map to its default state?
A: Refresh the page to reset all filters and parameters.

### Q: Can I download the data shown in the charts or maps?
A: Currently, data download functionality is not available. Contact the administrator for data access.

### Q: Why is the warming stripes chart not showing any data?
A: Ensure that the selected date range has data available. If the issue persists, check the dataset configuration.

---

This guide provides a comprehensive overview of the dashboard application. For further assistance, contact the support team.