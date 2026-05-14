import json
import os
import re
import uuid
from datetime import datetime

from celery_singleton import Singleton
from django.core.files import File
from django.utils.text import slugify
from loguru import logger

from climweb.config.celery import app


def _convention_to_regex(convention):
    """
    Convert a filename convention pattern to a named-group regex.

    Supports subdirectory paths, e.g.:
      {yyyy}/Bulletin_de_vigilance_nationale_du_{dd}-{mm}-{yyyy}

    If a variable appears more than once, the first occurrence becomes a
    named capturing group and subsequent ones become backreferences so the
    same value must appear in both positions.
    """
    pattern = re.escape(convention)
    seen = set()
    for var, name, digits in [
        (r'\{yyyy\}', 'yyyy', r'\d{4}'),
        (r'\{mm\}',   'mm',   r'\d{2}'),
        (r'\{dd\}',   'dd',   r'\d{2}'),
        (r'\{hh\}',   'hh',   r'\d{2}'),
    ]:
        while var in pattern:
            if name not in seen:
                pattern = pattern.replace(var, f'(?P<{name}>{digits})', 1)
                seen.add(name)
            else:
                pattern = pattern.replace(var, f'(?P={name})', 1)
    return re.compile(r'^' + pattern + r'$')


def _parse_datetime(match):
    """Extract a datetime from a regex match produced by _convention_to_regex."""
    g = match.groupdict()
    year = int(g.get('yyyy', 2000))
    month = int(g.get('mm', 1))
    day = int(g.get('dd', 1))
    hour = int(g.get('hh', 0))
    return datetime(year, month, day, hour, 0, 0)


def _datetime_slug(variable_name, dt):
    return f"{variable_name}_{dt.strftime('%Y_%m_%d_%H_00_00')}"


def _get_or_create_product_item_page(product_page, variable_name, dt):
    from climweb.pages.products.models import ProductItemPage

    slug = _datetime_slug(variable_name, dt)
    title = slug.replace('_', ' ').title()

    existing = ProductItemPage.objects.filter(
        slug=slug,
        path__startswith=product_page.path,
        depth=product_page.depth + 1,
    ).first()
    if existing:
        return existing, False

    page = ProductItemPage(
        title=title,
        slug=slug,
        date=dt.date(),
        products=json.dumps([]),
    )
    product_page.add_child(instance=page)
    revision = page.save_revision()
    revision.publish()
    logger.info(f"[INGESTION] Created ProductItemPage: {slug}")
    return page, True


def _create_wagtail_image(file_path, title):
    from wagtail.images import get_image_model
    Image = get_image_model()
    with open(file_path, 'rb') as f:
        image = Image(title=title)
        image.file.save(os.path.basename(file_path), File(f), save=True)
    return image


def _create_wagtail_document(file_path, title):
    from climweb.base.models import CustomDocumentModel
    with open(file_path, 'rb') as f:
        doc = CustomDocumentModel(title=title)
        doc.file.save(os.path.basename(file_path), File(f), save=True)
    return doc


def _get_products_raw(page):
    """
    Return the products StreamField as a plain list of block dicts.
    stream_data was removed in Wagtail 6+; use stream_block.get_prep_value()
    which serialises the StreamValue back to the list format used by JSONField.
    """
    from climweb.pages.products.models import ProductItemPage
    page_obj = ProductItemPage.objects.get(pk=page.pk)
    return page_obj.products.stream_block.get_prep_value(page_obj.products) or []


def _save_products_raw(page, raw):
    """
    Write the raw block list back to the products StreamField.
    Django's JSONField (use_json_field=True) serialises the list automatically.
    """
    from climweb.pages.products.models import ProductItemPage
    ProductItemPage.objects.filter(pk=page.pk).update(products=raw)


def _append_image_block(page, item_type_pk, effective_date, image_pk):
    """Append an image_product block to the page's products StreamField."""
    raw = _get_products_raw(page)
    date_str = effective_date.isoformat()

    for block in raw:
        if (block.get('type') == 'image_product'
                and str(block.get('value', {}).get('product_type')) == str(item_type_pk)
                and block.get('value', {}).get('date') == date_str):
            return

    raw.append({
        'type': 'image_product',
        'id': str(uuid.uuid4()),
        'value': {
            'product_type': str(item_type_pk),
            'date': date_str,
            'valid_until': None,
            'image': image_pk,
            'description': '',
        },
    })
    _save_products_raw(page, raw)


def _append_document_block(page, item_type_pk, effective_date, doc):
    """Append a document_product block to the page's products StreamField."""
    raw = _get_products_raw(page)
    date_str = effective_date.isoformat()

    for block in raw:
        if (block.get('type') == 'document_product'
                and str(block.get('value', {}).get('product_type')) == str(item_type_pk)
                and block.get('value', {}).get('date') == date_str):
            return

    thumbnail = doc.get_thumbnail()

    raw.append({
        'type': 'document_product',
        'id': str(uuid.uuid4()),
        'value': {
            'product_type': str(item_type_pk),
            'date': date_str,
            'valid_until': None,
            'document': doc.pk,
            'auto_generate_thumbnail': False,
            'thumbnail': thumbnail.pk if thumbnail else None,
            'description': '',
        },
    })
    _save_products_raw(page, raw)


def _resolve_watch_root(watch_root):
    """
    Resolve watch_root to an absolute path.
    A relative path is joined against MEDIA_ROOT, so editors can type
    'products' instead of '/full/path/to/media/products'.
    """
    if os.path.isabs(watch_root):
        return watch_root
    from django.conf import settings
    return os.path.join(settings.MEDIA_ROOT, watch_root)


def _ingest_product(product):
    from climweb.base.models import IMAGE_FORMATS
    from climweb.pages.products.models import ProductIngestedFile, ProductPage

    if not product.watch_root or not product.variable_name:
        logger.warning(f"[INGESTION] Product '{product.name}' missing watch_root or variable_name, skipping.")
        return

    product_page = ProductPage.objects.filter(product=product).live().first()
    if not product_page:
        logger.warning(f"[INGESTION] No live ProductPage found for product '{product.name}', skipping.")
        return

    watch_root = _resolve_watch_root(product.watch_root)
    variable_dir = os.path.join(watch_root, product.variable_name)
    if not os.path.isdir(variable_dir):
        logger.warning(f"[INGESTION] Variable directory not found: {variable_dir}")
        return

    for category in product.categories.all():
        fmt = (category.category_format or '').lower().strip()
        if not fmt:
            continue

        format_dir = os.path.join(variable_dir, fmt)
        if not os.path.isdir(format_dir):
            continue

        for item_type in category.product_item_types.all():
            convention = item_type.file_name_convention
            if not convention:
                continue

            try:
                pattern = _convention_to_regex(convention)
            except re.error as exc:
                logger.error(f"[INGESTION] Invalid convention pattern '{convention}': {exc}")
                continue

            for dirpath, _, filenames in os.walk(format_dir):
              for filename in filenames:
                _, ext = os.path.splitext(filename)
                if ext.lstrip('.').lower() != fmt:
                    continue

                file_path = os.path.join(dirpath, filename)
                # Match against the relative path from format_dir (forward slashes)
                # so conventions like {yyyy}/prefix_{dd}-{mm}-{yyyy} work correctly.
                rel_stem = os.path.relpath(file_path, format_dir)
                rel_stem = os.path.splitext(rel_stem)[0].replace(os.sep, '/')

                match = pattern.match(rel_stem)
                if not match:
                    continue
                file_mtime = os.path.getmtime(file_path)

                existing = ProductIngestedFile.objects.filter(
                    product=product, file_path=file_path
                ).first()
                if existing and existing.file_mtime == file_mtime:
                    continue

                try:
                    dt = _parse_datetime(match)
                except (ValueError, KeyError) as exc:
                    logger.error(f"[INGESTION] Could not parse datetime from '{filename}': {exc}")
                    continue

                product_item_page, _ = _get_or_create_product_item_page(
                    product_page, product.variable_name, dt
                )

                title = f"{product.name} {dt.strftime('%Y-%m-%d %H:00')}"
                is_image = fmt in IMAGE_FORMATS

                if is_image:
                    media_obj = _create_wagtail_image(file_path, title)
                    _append_image_block(product_item_page, item_type.pk, dt.date(), media_obj.pk)
                else:
                    media_obj = _create_wagtail_document(file_path, title)
                    _append_document_block(product_item_page, item_type.pk, dt.date(), media_obj)

                ProductIngestedFile.objects.update_or_create(
                    product=product,
                    file_path=file_path,
                    defaults={
                        'file_mtime': file_mtime,
                        'product_item_page': product_item_page,
                    },
                )
                logger.info(f"[INGESTION] Ingested: {file_path} → page '{product_item_page.slug}'")


@app.task(base=Singleton, bind=True)
def ingest_product_files(self):
    """Scan watch folders for all ingestion-enabled products and publish new files."""
    from climweb.base.models import Product

    products = Product.objects.filter(ingestion_enabled=True)
    logger.info(f"[INGESTION] Starting scan for {products.count()} enabled product(s).")

    for product in products:
        try:
            _ingest_product(product)
        except Exception as exc:
            logger.exception(f"[INGESTION] Error processing product '{product.name}': {exc}")

    logger.info("[INGESTION] Scan complete.")


@app.on_after_finalize.connect
def setup_product_ingestion_tasks(sender, **kwargs):
    sender.add_periodic_task(
        60 * 5,  # every 15 minutes
        ingest_product_files.s(),
        name='ingest-product-files-every-5-minutes',
    )
