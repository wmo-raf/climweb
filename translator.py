from deep_translator import GoogleTranslator
import polib

from django.conf import settings

po_file = polib.pofile('products/locale/es/LC_MESSAGES/django.po')

for entry in po_file:
    if not entry.translated():
        translation = GoogleTranslator(source='auto', target='es').translate(entry.msgid)
        entry.msgstr = translation
        # entry.flags.append('fuzzy')

po_file.save('products/locale/es/LC_MESSAGES/django.po')


