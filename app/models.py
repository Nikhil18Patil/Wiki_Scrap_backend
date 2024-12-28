from django.db import models
import uuid
# Models
class WikiPage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    url = models.URLField()
    timestamp = models.DateTimeField(auto_now_add=True)

class InfoBoxField(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)

class InfoBoxValue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    value = models.CharField(max_length=255)
    field = models.ForeignKey(InfoBoxField, on_delete=models.CASCADE)
    page = models.ForeignKey(WikiPage, on_delete=models.CASCADE)
