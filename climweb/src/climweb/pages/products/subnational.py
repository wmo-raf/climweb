from django.http import QueryDict


def boundary_svg(geom, size=100):
    """
    Render a boundary geometry as a simplified SVG outline, used as a listing thumbnail when a
    subnational product has no image. Returns a dict with the viewBox and path data.
    """
    min_x, min_y, max_x, max_y = geom.extent
    width, height = max_x - min_x, max_y - min_y
    if not width or not height:
        return None

    scale = size / max(width, height)
    simplified = geom.simplify(max(width, height) / 200, preserve_topology=True)

    # Polygon or MultiPolygon
    polygons = simplified if simplified.geom_type == "MultiPolygon" else [simplified]

    path = []
    for polygon in polygons:
        for ring in polygon:
            points = [f"{(x - min_x) * scale:.1f} {(max_y - y) * scale:.1f}" for x, y in ring.coords]
            path.append("M" + " L".join(points) + " Z")

    return {
        "view_box": f"0 0 {width * scale:.1f} {height * scale:.1f}",
        "path": " ".join(path),
    }


def querystring(request, **changes):
    """
    The current query string with the given params replaced, or removed when set to None.
    Pagination is always reset.
    """
    params = request.GET.copy() if request else QueryDict(mutable=True)
    params.pop("page", None)

    for key, value in changes.items():
        if value is None:
            params.pop(key, None)
        else:
            params[key] = value

    encoded = params.urlencode()
    return f"?{encoded}" if encoded else "?"
