from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_file_size(value):
    # 10 MB limit for images and 50 MB for PDFs
    limit = 10 * 1024 * 1024  # 10 MB in bytes
    if value.name.lower().endswith('.pdf'):
        limit = 50 * 1024 * 1024  # 50 MB for PDFs
    
    if value.size > limit:
        raise ValidationError(
            _('File too large. Size should not exceed %(limit)s MB.'),
            params={'limit': limit // (1024 * 1024)},
        ) 