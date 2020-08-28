from django.contrib import admin
from . import models

admin.site.register(models.Waypoint)
admin.site.register(models.WaypointCategory)
admin.site.register(models.Track)
admin.site.register(models.LinRegModel)
