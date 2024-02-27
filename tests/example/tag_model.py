from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy


class CustomTag(models.Model):
    # Generic foreign key setup via Django's ContentType mechanism
    content_object = GenericForeignKey("content_type", "object_id")
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.IntegerField(verbose_name=_("object ID"), db_index=True)

    # Tag stuff
    category = models.CharField(db_index=True, default="custom", max_length=200, null=False)
    name = models.CharField(
        db_index=True, max_length=255, verbose_name=pgettext_lazy("A tag name", "name")
    )
    confidence = models.FloatField()
