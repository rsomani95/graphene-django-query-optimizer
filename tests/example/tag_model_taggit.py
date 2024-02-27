from django.db import models
from django.utils.translation import pgettext_lazy
from taggit.models import GenericTaggedItemBase, TagBase

# The name `TaggableManager` is misleading, as this is actually a custom many to many `RelatedField`
# from taggit.managers import TaggableManager as TaggableManyToManyRelatedField


class Tag(TagBase):
    category = models.CharField(db_index=True, default="custom", max_length=200, null=False)
    name = models.CharField(
        db_index=True, max_length=255, verbose_name=pgettext_lazy("A tag name", "name")
    )


class TaggedItem(GenericTaggedItemBase):
    class Meta:
        unique_together = [["content_type", "object_id", "tag"]]

    tag = models.ForeignKey(Tag, related_name="custom_tagged_items", on_delete=models.CASCADE)
    confidence = models.FloatField()
