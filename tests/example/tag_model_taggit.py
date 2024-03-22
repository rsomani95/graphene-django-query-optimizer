from django.db import models
from django.utils.translation import pgettext_lazy
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel, UUIDModel
from model_utils.fields import UUIDField
from taggit.models import GenericTaggedItemBase, TagBase, GenericUUIDTaggedItemBase, CommonGenericTaggedItemBase

# The name `TaggableManager` is misleading, as this is actually a custom many to many `RelatedField`
# from taggit.managers import TaggableManager as TaggableManyToManyRelatedField


class Tag(TagBase):
    category = models.CharField(db_index=True, default="custom", max_length=200, null=False)
    name = models.CharField(
        db_index=True, max_length=255, verbose_name=pgettext_lazy("A tag name", "name")
    )


class TaggedItem(GenericTaggedItemBase):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("content_type", "object_id", "tag"),
                name="taggit_taggeditem_content_type_id_object_id_tag_id_4bb97a8e_uniq1",
            )
        ]

    tag = models.ForeignKey(Tag, related_name="custom_tagged_items", on_delete=models.CASCADE)
    confidence = models.FloatField()


# NOTE: `GenericUUIDTaggedItemBase` defines its UUID field to be `models.UUID` field, which is
# NOT THE SAME AS OUR UUID FIELD
class TaggedItemDefaultUUID(GenericUUIDTaggedItemBase):
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("content_type", "object_id", "tag"),
                name="taggit_taggeditem_content_type_id_object_id_tag_id_4bb97a8e_uniq2",
            )
        ]

    tag = models.ForeignKey(Tag, related_name="custom_tagged_items_default_uuid", on_delete=models.CASCADE)
    confidence = models.FloatField()


# class TaggedItemProperUUID(CommonGenericTaggedItemBase):
#     class Meta:
#         constraints = [
#             models.UniqueConstraint(
#                 fields=("content_type", "object_id", "tag"),
#                 name="taggit_taggeditem_content_type_id_object_id_tag_id_4bb97a8e_uniq",
#             )
#         ]

#     object_id = UUIDField(verbose_name=_("object ID"), db_index=True)
#     tag = models.ForeignKey(Tag, related_name="custom_tagged_items_proper_uuid", on_delete=models.CASCADE)
#     confidence = models.FloatField()