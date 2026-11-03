from django.db import migrations


def copy_flagged_items(apps, schema_editor):
    """
    Updates and events used to be picked by a site-wide "Anticipatory Action" checkbox on news,
    publication and event pages. Copy what each page showed into its own chooser lists,
    using the same selection as before, so nothing disappears.
    """
    AnticipatoryActionPage = apps.get_model("anticipatory_action", "AnticipatoryActionPage")
    AnticipatoryActionUpdate = apps.get_model("anticipatory_action", "AnticipatoryActionUpdate")
    AnticipatoryActionEvent = apps.get_model("anticipatory_action", "AnticipatoryActionEvent")
    NewsPage = apps.get_model("news", "NewsPage")
    PublicationPage = apps.get_model("publications", "PublicationPage")
    EventPage = apps.get_model("events", "EventPage")

    news = list(NewsPage.objects.filter(live=True, is_anticipatory_action=True)
                .order_by("-is_featured", "-date")[:2])
    publications = list(PublicationPage.objects.filter(live=True, is_anticipatory_action=True)
                        .order_by("-featured", "-publication_date")[:4 - len(news)])
    events = list(EventPage.objects.filter(live=True, is_anticipatory_action=True, is_archived=False,
                                           is_hidden=False).order_by("-date_from")[:3])

    for page in AnticipatoryActionPage.objects.all():
        if not AnticipatoryActionUpdate.objects.filter(page=page).exists():
            for order, update in enumerate(news + publications):
                AnticipatoryActionUpdate.objects.create(page=page, update_id=update.pk, sort_order=order)

        if not AnticipatoryActionEvent.objects.filter(page=page).exists():
            for order, event in enumerate(events):
                AnticipatoryActionEvent.objects.create(page=page, event_id=event.pk, sort_order=order)


class Migration(migrations.Migration):
    dependencies = [
        ("anticipatory_action", "0005_update_and_event_choosers"),
        ("news", "0008_optional_alt_image_block"),
        ("publications", "0008_publicationpage_is_anticipatory_action"),
        ("events", "0009_eventpage_is_anticipatory_action"),
    ]

    operations = [
        migrations.RunPython(copy_flagged_items, migrations.RunPython.noop),
    ]
