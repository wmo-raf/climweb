from django.core.management.base import BaseCommand, CommandError
from wagtail.models import Site

from climweb.pages.anticipatory_action.setup import create_draft_page, get_home_page


class Command(BaseCommand):
    help = ("Creates a draft Anticipatory Action page from the template under the home page, "
            "if the site does not have one yet")
    
    def add_arguments(self, parser):
        parser.add_argument("--site", type=int, help="ID of the site to create the page in. Defaults to the default site")
    
    def handle(self, *args, **options):
        site_id = options.get("site")
        try:
            site = Site.objects.get(pk=site_id) if site_id else Site.objects.get(is_default_site=True)
        except Site.DoesNotExist:
            raise CommandError("Site not found")
        
        home_page = get_home_page(site)
        if home_page is None:
            raise CommandError("The site's root page is not a Home Page")
        
        page, created = create_draft_page(home_page, site=site)
        
        if created:
            self.stdout.write(self.style.SUCCESS(
                f"Created draft Anticipatory Action page '{page.title}' (id {page.pk}) at /{page.slug}/ "
                f"from the template. Replace the example content and publish it from the admin"
            ))
        else:
            self.stdout.write(f"An Anticipatory Action page already exists: '{page.title}' (id {page.pk})")
