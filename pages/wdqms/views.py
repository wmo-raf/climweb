from django.shortcuts import render
import json
from adminboundarymanager.models import AdminBoundarySettings

from climweb_wdqms.models import Station,Transmission
from django.db.models.functions import TruncMonth
from django.db.models import Max
# Create your views here.


def wdqms_reports(request):

    stations = Station.objects.all()
    transmissions = Transmission.objects.all()
    variables = []
    latest_date = None
    years = []

    if transmissions:
        variables = transmissions.values_list('variable', flat=True).distinct()
        years = transmissions.values_list('received_date__year', flat=True).distinct()
        latest_date = transmissions.filter(variable=variables[0]).order_by('received_date').values_list('received_date__date',  flat=True).last()

    abm_settings = AdminBoundarySettings.for_request(request)

    abm_extents = abm_settings.combined_countries_bounds

    return render(request, "wdqms/report_index.html", {
        'stations': stations,
        'variables':variables,
        'latest_date':latest_date,
        'years':years,
        'bounds':abm_extents,
    })