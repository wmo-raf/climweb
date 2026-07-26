# Creating and publishing Web Stories

## Introduction

Web Stories are short, full-screen videos(similar to those found on various social media platforms) built on Google's open Web Stories standard. They are designed for quick, mobile-first storytelling using images, videos and short texts that readers tap through one at a time.

For National Meteorological and Hydrological Service(NMHS), Web Stories are a good fit for content that benefits from a quick visual format rather than a a long article. For example, a seasonal outlook explainer or public awareness campaign.

In ClimWeb, Web Stories are managed from the **Web Stories** section. Published stories are automatically included in the site's sitemap, hence making them easier to search for.

This guide walks through the full workflow: Creating a story, adding and ordering slides, adding media and text overlays, previewing, publishing and managing stories after they are published.

![Web Stories landing page](../_static/images/webstories/01_landing_page.png "Web Stories landing page")

## Prerequisites

Before creating your first Web Story, verify the following, especially on a freshly installed instance:

1. **A Home Page must exist and be published.** 
A fresh ClimWeb checkout has no pages beyond Wagtail's generic "Welcome to your new Wagtail site" placeholder. Create and publish a real Home Page first (select *Pages*, select *Add child page*, fill in required fields, Publish), and confirm it is set as the site's root page under *Settings*, *Sites*.

2. **A Web Stories listing page must exist and be published as a child of Home page.**
Without one, the Web Stories dashboard (`/cms-admin/web-stories-list/`) returns a server error, and the editor may not function correctly. To create it: select *Pages*, open *Home*, select *Add child page*, select *Web Story List Page*, give it a title (e.g. "Web Stories"), select *Publish*. Only one instance of this page is needed per site.

## Creating a story

1. Go to **Web Stories** in the using the Navigation menu on the left side of the screen.

> **Note 1 - Navigation menu toggle:** The navigation menu can be expanded or collapsed using the arrow button(|-> OR <-| respectively).

![Web Stories page with collapsed menu](../_static/images/webstories/02_landing_page_collapsed_menu.png "Web Stories page with collapsed menu")

2. Click **Create New Story**.

> **Note 2 - Mobile navigation menu behavior:** On smaller screens, the navigation menu may shrink into a menu button (three horizontal lines inside a black square) located in the top-left corner of the screen. Tap or click this button to open the menu.

> **Note 3 - Dashboard menu collapsing:** Like **Note 2**, the **Create New Story** button may be shrunk into a menu button (three horizontal lines with a white background, next to the "Dashboard" title). Tap or click this button to open the menu.

<div style="display: flex; gap: 10px; align-items: flex-start;">
  <img src="../_static/images/webstories/03_landing_page_small_screen_collapsed_menu.png" alt="Small screen with the navigation menu collapsed" title="Collapsed Menu View" style="width: 32%;" />
  <img src="../_static/images/webstories/04_landing_page_small_screen_expanded_menu.png" alt="Small screen with the navigation menu expanded" title="Expanded Menu View" style="width: 32%;" />
  <img src="../_static/images/webstories/05_landing_page_small_screen_expanded_menu_create_webstories.png" alt="Small screen showing the expanded Web Stories specific menu" title="Web Stories Menu View" style="width: 32%;" />
</div>

3. Fill in the story title, then save as a draft:
![Web Stories editing canvas](../_static/images/webstories/06_webstories_editing_canvas.png "Web Stories editing canvas")

> **Note 4 - Missing title default** A story can be published with a blank title, ClimWeb will default the title to "Untitled." in this scenario.

4. Save the story by selecting *Save draft* in the bottom left of the screen. The other fields will be covered later in this guide (see Media and text overlays and Publishing).

> **Note 5 - Content drafting workflow:** You can create the story with just a title first, then build out content. You do not need to have every field filled in before adding content.

## Adding slides

Each story is made up of a sequence of slides. ClimWeb's slide editor supports a few different content types:

- **Image slide**: An image of PNG, JPG, AVIF, GIF, JPEG, or WEBP format, with a maximum filesize of 10.0 MB.

- **Video slide**: A video of AVI, H264, M4V, MKV, MOV, MP4, MPEG, MPG, OGV, or WEBM format. There is no video-specific filesize limit enforced by the editor. However the practical ceiling is the server's general upload limit of 25.0 MB by default. and may be lower if a reverse proxy in front of ClimWeb imposes its own limit.

- **Third-party media**: In addition to user uploaded images and video, the Insert panel includes a third-party stock media tab (photos, video, and GIFs from Unsplash, Cover, and Tenor) powered by Google's Media 3P proxy API. This works out of the box with no ClimWeb-side configuration required as the integration ships with the editor itself. Do note that all third-party assets are subject to the intellectual property and licensing policies of their respective platforms. Users are responsible for ensuring their use complies with these terms.

- **Shapes, stickers, and pre-built page templates**: These features are available from the Insert panel and when creating a new story. They are a fixed library built into the editor; they cannot be extended or supplemented with additional content. The search field matches only whole words within an item's name. For example, searching "fresh and bright" returns an item named "Fresh and Bright Cover", but searching "cover" alone does not. Category terms such as "Cover", "Section", or "Quote" are not matched by the search field; use the filter buttons below the search bar to filter by these instead.

To add a slide:

1. Open your story and click **+ New Page**.
3. Build out the slide's content (see [Media and text overlays](#media-and-text-overlays) below).
3. Repeat until you have all the slides you need.

![Web Stories editing canvas with additional pages](../_static/images/webstories/07_webstories_editing_canvas_additional_pages.png "Web Stories editing canvas with additional pages")

> **Note 6 - Google distribution guidelines:** Google’s Web Stories format recommends a minimum of 4 pages to be eligible for indexing, organic Search, and appearance on the Google Discover feed. Stories shorter than 4 pages are deemed incomplete by Google's guidelines and are typically suppressed from distribution ([Source: Google Search Central](https://developers.google.com/search/docs/appearance/web-stories-creation-best-practices)).

> **Note 7 - ClimWeb editor enforcement:**ClimWeb’s Web Story editor does not enforce this minimum page requirement at either the backend (Django) or frontend levels. While the underlying Web Stories editor contains a built-in pre-publish checklist helper, the editor does not block or pop up warnings during the publishing workflow if a story is under 4 pages or contains blank slides. Authors can successfully save and publish stories with only 2–3 slides, but should manually ensure they meet the 4-page minimum to guarantee search engine visibility.

## Media and text overlays

### Adding images

1. On a slide, open the **Insert** tab in the left panel.
2. Click the **upload icon** (cloud with an up arrow) in the row of small icons below the search bar, it sits between the **link** icon and the **video** icon.
3. In the dialog that opens, use the **Upload** tab to add a new file, or switch to the **Search** tab to choose an existing image from ClimWeb's media library.
4. Supported formats are PNG, JPG, AVIF, GIF, JPEG, and WEBP, with a maximum file size of 10.0 MB per image.
5. Adjust image on canvas as desired.

![Insert panel with the upload icon highlighted](../_static/images/webstories/08_media_upload_dialog.png "Insert panel, upload icon")

![Upload tab of the image chooser](../_static/images/webstories/09_image_upload_tab.png "Image upload, Upload tab")

![Search tab of the image chooser, showing existing library images available to insert](../_static/images/webstories/10_image_search_tab.png "Image chooser, Search tab")

![Slide with an image inserted, showing resize handles and the transform toolbar](../_static/images/webstories/11_slide_with_image.png "Slide with image, no text yet")

![Slide with an image inserted, after user adjustments](../_static/images/webstories/12_slide_with_image_adjusted.png "Slide with image after adjustments")

> **Note 8 - Entering tags when uploading images:** Press "Enter" after typing in individual tags to enter them. Multi-word tags with spaces will automatically be enclosed in double quotes(" ") by ClimWeb.

> **Important Note - Known Limitation:** The image selection list in the side panel can only show the first 20 images uploaded to the website. If the site has more than 20 images, any new images you upload will **not** appear in this browseable side list.
> **What this means for you:**
> * **New uploads still work:** You can safely click the upload button to add new images. Your files are saved properly, even if they disappear from the side list right after.
> * **Existing stories are safe:** Any images already placed inside your Web Story slides will display and publish perfectly.
> * **Where to find all images:** If you need to see, edit, or manage your full library of pictures, use the main website dashboard under the **Images** section instead of the Web Story editor's side panel.
> 
> This is a known display issue with the side list itself, not a sign that your upload failed. [Issue link: https://github.com/erick-otenyo/wagtail-webstories-editor/issues/2].

### Adding text overlay

1. With the slide open, click on the desired text types to add them to the canvas (or drag desired text types to add them to the canvas).
2. Use the text toolbar to adjust font, size, colour, alignment, and position on the slide.
3. Drag the text box to position it over the media so it stays readable (avoid busy parts of the image).

![Slide with text types added, before text has been updated](../_static/images/webstories/13_slide_image_and_text.png "Slide with text types")

![Slide with text that has been completed](../_static/images/webstories/14_slide_image_and_text_complete.png "Slide with text completed")

> **Note 9 – Text Manipulation and Scaling:** To reposition a text element on the canvas, click and drag within the text box boundaries. You must ensure the element is not in active text-editing (typing) mode. If the typing cursor is active, dragging will select text rather than move the container. To move the element, click outside the box to deselect it, then click once to select and drag it. Additionally, dragging the corner handles of the bounding box will dynamically scale the font size proportionally. To adjust the box width or wrap text without changing the font size, use the manual width and height inputs or the dedicated font size selector in the right-hand styling properties panel.

## Ordering slides

Slides play in the order they appear in the story's slide list.

1. Open the slide panel along the bottom of the editor.
2. Drag a slide thumbnail to a new position to reorder it.

![Slide thumbnail strip showing multiple slides in sequence](../_static/images/webstories/15_slide_thumbnail_strip.png "Slide order panel")

![Slides after being reordered](../_static/images/webstories/16_slide_reordered.png "Reordered slides")

> **Note 10 – Opening the slide panel:** The slide panel is open by default in the editor. The slide panel can be expanded or collapsed using the 'page' indicator (marked in red in the following image).
![Slide panel collapsed](../_static/images/webstories/17_collapsed_slide_panel.png "Collapsed slide panel")

> **Note 11 – reordering slides:** All slide, including the first slide can be reordered. 

## Previewing

Before publishing, preview the story to see how it will actually look and feel to a reader.

1. Click **Preview** (mobile phone icon at the top right of the screen) in the story editor.
![Preview button](../_static/images/webstories/18_preview_button.png "Preview button")

2. The preview function lets you tap/click through each slide as a reader would in mobile, tablet and browser formats.
<div style="display: flex; gap: 10px; align-items: flex-start;">
  <img src="../_static/images/webstories/19_mobile_preview.png" alt="Mobile preview" style="height: 400px; width: auto;" />
  <img src="../_static/images/webstories/20_tablet_preview.png" alt="Tablet preview" title="Expanded Menu View" style="height: 400px; width: auto;" />
  <img src="../_static/images/webstories/21_browser_preview.png" alt="Browser preview" title="Web Stories Menu View" style="height: 400px; width: auto;" />
</div>

> **Note 12 - previewing changes:** Do note that any changes made must be saved using the **Save draft** button before it is reflected in the previews 

> **Note 13 - preview in a separate browser tab:** As Web Stories are built for mobile, there is a built-in function that allows previews to reflect that of a mobile platform as closely as possible.
![Preview in a separate browser tab](../_static/images/webstories/22_seperate_preview.png "Preview in a separate browser tab")

## Publishing

1. Once the story is complete, click **Publish**.
2. **Pre-publish Validation:** Clicking **Publish** instantly publishes the Web Story directly without a confirmation dialog or pre-publish check.

### Cover image requirement

Google's Web Stories format recommends setting a cover/poster image. However, ClimWeb’s editor currently does not enforce pre-publish validation checks. 

> **Note 14 - Observed Behavior:**
> - **Validation / Enforcements:** None. There is no validation blocking publication, nor are there warning prompts before publishing.
> - **Publishing without a Cover Image:** You can successfully publish a story without selecting or uploading a cover/poster image. No error message is shown, and a blank placeholder is assigned.
> - **Publishing without a Title:** You can publish a story with a blank title. When published in this state, ClimWeb defaults the title to `"Untitled."`.

![Published story without title and cover image](../_static/images/webstories/23_published_story_blank.png "Published story without title and cover image")

### Setting a cover image

1. **Story Title:** Click on the word **Untitled** to edit the story's main title.
2. **Cover Image:** On the editing panel on right of the screen, click on **Document**. Use the **Poster image** field under the **Publishing** header to set the cover image of the story.

![Setting title and cover image](../_static/images/webstories/24_setting_cover_img_and_title.png "Editing title and cover image")

## Managing published stories

- Published and draft stories are both listed in the **Web Stories** section, with a status indicator for each.
![Draft and published stories](../_static/images/webstories/25_draft_and_published_stories.png "Draft and published stories")

- To make edits after publishing, open the story, make your changes, and republish the story.

- To take a story down, open the story editor and select **Unpublish** from the same menu as **Save draft**. This removes it from the public listing without deleting it.

- To permanently remove a story, use the **Delete** action from the same menu as **Save draft**.
![Unpublish](../_static/images/webstories/26_unpublish.png "Unpublish")


## Troubleshooting

| Problem | Likely cause | What to do |
|---|---|---|
| Navigating to `/cms-admin/web-stories-list/` results in a Server Error (500), or the Web Story editor fails to function properly. | Missing Home Page or missing Web Story List Page child page.| Ensure a published Home Page exists under **Pages** and is assigned as the root page in **Settings** to **Sites**. Next, open the Home Page in the admin, select **Add child page**, choose **Web Story List Page**, give it a title (e.g. "Web Stories"), and click **Publish**. (Only one instance is required per site). |
| Story is published but not visible on the public site | The Web Stories listing page is not configured, or has not been published itself | Ask your administrator to confirm the listing page is set up and published |
