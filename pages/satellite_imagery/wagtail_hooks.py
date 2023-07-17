from wagtail import hooks


@hooks.register("register_icons")
def register_icons(icons):
    return icons + [
        'wagtailfontawesomesvg/solid/palette.svg',
        'wagtailfontawesomesvg/solid/database.svg',
        'wagtailfontawesomesvg/solid/layer-group.svg',
        'wagtailfontawesomesvg/solid/globe-africa.svg',
        'wagtailfontawesomesvg/solid/map.svg',
    ]
