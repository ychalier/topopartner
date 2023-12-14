from django.contrib import admin
from . import models

admin.site.register(models.Track)
admin.site.register(models.LinRegModel)
admin.site.register(models.ApiKey)
