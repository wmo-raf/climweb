# from celery.result import AsyncResult
# from wagtail.contrib.forms.views import SubmissionsListView

# from wagtailzoom.models import ZoomBatchRegistration
# from core.utils import get_object_or_none


# class CustomSubmissionsListView(SubmissionsListView):
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         event_reg_page = context.get('form_page')
#         if event_reg_page:
#             batch_reg_enabled = event_reg_page.batch_zoom_reg_enabled

#             if batch_reg_enabled and not event_reg_page.event.is_ended and event_reg_page.can_add_to_zoom() and \
#                     event_reg_page.enable_adding_registrants:
#                 batch_reg = get_object_or_none(ZoomBatchRegistration, event_registration_page=event_reg_page)
#                 if batch_reg:
#                     context.update({
#                         "batch_reg_id": batch_reg.id,
#                         "added_to_zoom": batch_reg.processed_submissions_count,
#                         "pending": batch_reg.pending_submissions_count
#                     })

#                     if batch_reg.task_id:
#                         result = AsyncResult(batch_reg.task_id)

#                         state = {
#                             'task_status': result.state,
#                             'task_details': result.info,
#                             'task_id': batch_reg.task_id
#                         }

#                         context.update({**state})

#         return context