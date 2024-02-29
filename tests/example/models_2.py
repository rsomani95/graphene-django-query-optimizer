from model_utils.models import TimeStampedModel, UUIDModel
from django.db import models
from taggit.managers import TaggableManager as TaggableManyToManyRelatedField
# from .tag_model_taggit import TaggedItemDefaultUUID, TaggedItemProperUUID
from .tag_model_taggit import TaggedItemDefaultUUID
import uuid

class BaseModel(UUIDModel, TimeStampedModel):
    class Meta:
        abstract = True


class Library(BaseModel):
    library_name = models.CharField(max_length=200)
    description = models.TextField(null=True, default=None)
    is_public = models.BooleanField(default=False)


class VideoAsset(BaseModel):
    library = models.ForeignKey(
        "Library", on_delete=models.CASCADE, null=True, default=None
    )
    time_base = models.IntegerField(default=600)
    duration = models.IntegerField(null=False, default=None)


# class SegmentDefaultTags(BaseModel):
#     category = models.CharField(db_index=True, max_length=200, null=False)
#     description = models.TextField(null=True)
#     video_asset = models.ForeignKey("VideoAsset", on_delete=models.CASCADE)
#     transcript = models.TextField(null=True)

#     tags = TaggableManyToManyRelatedField(blank=True, through=TaggedItemDefaultUUID)


class SegmentProperTags(TimeStampedModel):
    id = models.UUIDField(
        primary_key=True,
        editable=False,
        default=uuid.uuid4
    )

    category = models.CharField(db_index=True, max_length=200, null=False)
    description = models.TextField(null=True)
    video_asset = models.ForeignKey("VideoAsset", on_delete=models.CASCADE)
    transcript = models.TextField(null=True)

    # tags = TaggableManyToManyRelatedField(blank=True, through=TaggedItemProperUUID)
    tags = TaggableManyToManyRelatedField(blank=True, through=TaggedItemDefaultUUID)
