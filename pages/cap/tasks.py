from background_task import background
from wagtail.images.models import Image

from base.utils import get_object_or_none


@background(schedule=5)
def generate_cap_alert_card(cap_alert_page_id):
    from .models import (CapAlertPage)

    cap_alert_page = get_object_or_none(CapAlertPage, id=cap_alert_page_id)
    if cap_alert_page:
        try:
            # create summary image
            image_content_file = cap_alert_page.generate_alert_card_image()
            if image_content_file:
                # delete old image
                if cap_alert_page.search_image:
                    cap_alert_page.search_image.delete()

                # create new image
                cap_alert_page.search_image = Image(title=cap_alert_page.title, file=image_content_file)
                cap_alert_page.search_image.save()

                # save the instance
                cap_alert_page.save()

        except Exception as e:
            pass
