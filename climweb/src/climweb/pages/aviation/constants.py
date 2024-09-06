from django.utils.translation import gettext_lazy as _

CLOUD_COVER = [
    {"id": "broken", "name": "Broken"},
    {"id": "few", "name": "Few"},
    {"id": "no_significant_cloud", "name": "No Significant Cloud"},
    {"id": "other", "name": "Other"},
    {"id": "overcast", "name": "Overcast"},
    {"id": "scattered", "name": "Scattered"},
    {"id": "sky_clear", "name": "Clear"},
]

WIND_BARBS = []

for x in range(1, 23):
    WIND_BARBS.append({
        'id': f'barbs-{x}',
        'name': f'barbs-{x}',
    })

    WIND_BARBS.append({
        'id': f'barbs-{x}-flip',
        'name': f'barbs-{x}-flip'
    })
