from wagtail.api.v2.router import WagtailAPIRouter

from wagtail_webstories_editor.api_viewsets import (CustomImagesAPIViewSet,
                                                    CustomMediaAPIViewSet,
                                                    CustomDocumentAPIViewSet)


class ImagesAPIViewSet(CustomImagesAPIViewSet):
    pass


class MediaAPIViewSet(CustomMediaAPIViewSet):
    pass


class DocumentAPIViewSet(CustomDocumentAPIViewSet):
    pass


api_router = WagtailAPIRouter('wagtailapi')

api_router.register_endpoint('images', ImagesAPIViewSet)
api_router.register_endpoint("media", MediaAPIViewSet)
api_router.register_endpoint('documents', DocumentAPIViewSet)
