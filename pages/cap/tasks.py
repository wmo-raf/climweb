from background_task import background
from wagtailcache.cache import clear_cache

from base.utils import get_object_or_none
from pages.cap.utils import (
    create_cap_area_map_image,
    create_cap_pdf_document,
    get_first_page_of_pdf_as_image
)


@background(schedule=5)
def create_cap_alert_multi_media(cap_alert_page_id, clear_cache_on_success=False):
    from .models import CapAlertPage

    try:
        cap_alert = get_object_or_none(CapAlertPage, id=cap_alert_page_id)

        if cap_alert:
            print("[CAP] Generating CAP Alert MultiMedia content for: ", cap_alert.title)
            # create alert area map image
            cap_alert_area_map_image = create_cap_area_map_image(cap_alert)

            if cap_alert_area_map_image:
                print("[CAP] 1. CAP Alert Area Map Image created for: ", cap_alert.title)
                cap_alert.alert_area_map_image = cap_alert_area_map_image
                cap_alert.save()

                # create_cap_pdf_document
                cap_preview_document = create_cap_pdf_document(cap_alert, template_name="cap/alert_detail_pdf.html")
                cap_alert.alert_pdf_preview = cap_preview_document
                cap_alert.save()

                print("[CAP] 2. CAP Alert PDF Document created for: ", cap_alert.title)

                file_id = cap_alert.last_published_at.strftime("%s")
                preview_image_filename = f"{cap_alert.identifier}_{file_id}_preview.jpg"

                sent = cap_alert.sent.strftime("%Y-%m-%d-%H-%M")
                preview_image_title = f"{sent} - Alert Preview"

                # get first page of pdf as image
                cap_preview_image = get_first_page_of_pdf_as_image(file_path=cap_preview_document.file.path,
                                                                   title=preview_image_title,
                                                                   file_name=preview_image_filename)

                print("[CAP] 3. CAP Alert Preview Image created for: ", cap_alert.title)

                if cap_preview_image:
                    cap_alert.search_image = cap_preview_image
                    cap_alert.save()

                print("[CAP] CAP Alert MultiMedia content saved for: ", cap_alert.title)

                if clear_cache_on_success:
                    clear_cache()
        else:
            print("[CAP] CAP Alert not found for ID: ", cap_alert_page_id)
    except Exception as e:
        print("[CAP] Error in create_cap_alert_multi_media: ", e)
        pass
