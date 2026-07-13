import io

import matplotlib

matplotlib.use("Agg")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from climweb.pages.cityclimate.models import DataValue, THUMBNAIL_SIZE

# Django date-format choices (see CityClimateDataPage.PERIOD_CHOICES) mapped
# to their strftime equivalent for the thumbnail's x/y axis labels.
THUMBNAIL_DATE_FORMATS = {
    "day": "%d",
    "dayandmonth": "%d %b",
    "month": "%b",
    "monthandyear": "%b %Y",
    "year": "%Y",
}

THUMBNAIL_DPI = 100


def get_climatology_page_data(page_instance, city_id, date_as_str=False, param_key_field="id", params_as_dict=False):
    parameters = page_instance.data_parameters.all()
    if city_id:
        param_values = DataValue.objects.filter(city_id=city_id, parameter__in=parameters)
    else:
        param_values = DataValue.objects.filter(parameter__in=parameters)
    
    values_dict = {}
    
    for value in param_values:
        date_val = value.date.isoformat() if date_as_str else value.date
        
        param_data = {getattr(value.parameter, param_key_field): value.value}
        
        if not values_dict.get(date_val):
            values_dict[date_val] = {}
        
        if params_as_dict:
            if not values_dict[date_val].get("params_data"):
                values_dict[date_val]["params_data"] = {}
            values_dict[date_val]["params_data"].update(param_data)
        else:
            values_dict[date_val].update(param_data)
        
        values_dict[date_val].update({value.parameter.slug: value.value, "city": value.city.name,
                                      "coordinates": [float(coordinate) for coordinate in value.city.coordinates if
                                                      coordinate]})
    
    values = [{"date": key, **values_dict[key]} for key in values_dict.keys()]

    return values


def render_climate_chart_thumbnail(page, city, month=None, parameter_slugs=None):
    """
    Render a PNG snapshot of a city's climate chart for use as a social-share
    thumbnail (og:image). Facebook/WhatsApp/Telegram/LinkedIn/X crawlers
    don't run JavaScript, so the live Highcharts chart on the page can't be
    captured directly - this mirrors it server-side instead, using the same
    per-parameter chart type/colour configured in the page editor (see
    blocks.py).
    """
    enabled_parameters = list(page.data_parameters.filter(enabled=True))

    if parameter_slugs:
        wanted = set(parameter_slugs)
        selected = [p for p in enabled_parameters if p.slug in wanted] or enabled_parameters[:1]
    else:
        selected = enabled_parameters[:1]

    series = {}
    for parameter in selected:
        chart_config = {}
        for block in parameter.chart_config:
            chart_config = block.value.config
        series[parameter.slug] = {
            "parameter": parameter,
            "chart_type": chart_config.get("type", "line"),
            "color": chart_config.get("color") or "#2caffe",
            "dates": [],
            "values": [],
        }

    if city and selected:
        data_values = DataValue.objects.filter(
            city=city, parameter__in=selected
        ).select_related("parameter").order_by("date")

        for value in data_values:
            if value.value is None:
                continue
            if month and str(value.date.month) != str(month):
                continue
            series[value.parameter.slug]["dates"].append(value.date)
            series[value.parameter.slug]["values"].append(value.value)

    width, height = THUMBNAIL_SIZE
    fig, ax = plt.subplots(figsize=(width / THUMBNAIL_DPI, height / THUMBNAIL_DPI), dpi=THUMBNAIL_DPI)
    fig.patch.set_facecolor("white")

    has_data = False
    # a horizontal "bar" chart puts dates on the y-axis instead of x. Mixing
    # orientations on one chart doesn't make sense, so if any selected
    # parameter is horizontal, treat the whole thumbnail as horizontal.
    horizontal = any(s["chart_type"] == "bar" for s in series.values() if s["dates"])

    for s in series.values():
        if not s["dates"]:
            continue
        has_data = True
        chart_type = s["chart_type"]
        color = s["color"]
        name = s["parameter"].name

        bar_width = 0.8
        if chart_type in ("column", "bar"):
            d_nums = mdates.date2num(s["dates"])
            if len(d_nums) > 1:
                diffs = sorted(set(round(b - a, 3) for a, b in zip(d_nums[:-1], d_nums[1:])))
                bar_width = diffs[0] * 0.8 if diffs else 0.8

        if chart_type == "column":
            ax.bar(s["dates"], s["values"], label=name, color=color, width=bar_width)
        elif chart_type == "bar":
            ax.barh(s["dates"], s["values"], label=name, color=color, height=bar_width)
        elif chart_type == "area":
            ax.plot(s["dates"], s["values"], color=color, linewidth=1.5)
            ax.fill_between(s["dates"], s["values"], color=color, alpha=0.35)
            ax.plot([], [], color=color, label=name)  # legend proxy
        else:
            ax.plot(s["dates"], s["values"], label=name, color=color, linewidth=2)

    date_format = THUMBNAIL_DATE_FORMATS.get(page.time_format, "%Y-%m-%d")
    if horizontal:
        ax.yaxis.set_major_formatter(mdates.DateFormatter(date_format))
    else:
        ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format))
        fig.autofmt_xdate()

    title = page.title
    if city:
        title = f"{title} — {city.name}"
    ax.set_title(title, fontsize=16, fontweight="bold", pad=16)

    if has_data and len(selected) > 1:
        ax.legend(loc="upper right", fontsize=10, frameon=False)

    if not has_data:
        ax.text(0.5, 0.5, "No data available", ha="center", va="center",
                 transform=ax.transAxes, fontsize=14, color="#888888")
        ax.set_xticks([])
        ax.set_yticks([])

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#eeeeee")

    fig.tight_layout()

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=THUMBNAIL_DPI)
    plt.close(fig)
    buffer.seek(0)

    return buffer.getvalue()
