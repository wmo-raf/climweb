from wagtail import hooks


@hooks.register("register_icons")
def register_icons(icons):
    return icons + [
        'wagtailfontawesomesvg/solid/layer-group.svg',
    ]
