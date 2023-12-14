import datetime
import io

from django.db import models
from django.conf import settings
import gpxpy


class Track(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    label = models.CharField(max_length=255)
    comment = models.TextField(blank=True, null=True)
    illustration = models.URLField(blank=True, null=True)
    date_added = models.DateTimeField(auto_now=False, auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True, auto_now_add=False)
    date_visited = models.DateField(blank=True, null=True)
    is_recording = models.BooleanField(default=False)
    is_route = models.BooleanField(default=False)
    distance = models.FloatField(blank=True, null=True)
    uphill = models.FloatField(blank=True, null=True)
    downhill = models.FloatField(blank=True, null=True)
    duration = models.DurationField(blank=True, null=True)
    public = models.BooleanField(default=False)
    gpx = models.TextField()

    def __str__(self):
        if self.is_recording:
            return "[Recording] " + self.label
        if self.is_route:
            return "[Route] " + self.label
        return self.label

    def parsed(self):
        return gpxpy.parse(io.StringIO(self.gpx))

    def has_elevation_data(self):
        return "<ele>" in self.gpx

    def iter_trackpoints(self):
        for trk in self.parsed().tracks:
            for trkseg in trk.segments:
                for trkpt in trkseg.points:
                    yield trkpt

    def start(self):
        return next(self.iter_trackpoints())

    def pretty_duration(self):
        if self.duration is None:
            minutes = 0
        else:
            minutes = int(self.duration.total_seconds() / 60.)
        hours = minutes // 60
        string = "%dh" % hours
        minutes -= 60 * hours
        string += str(minutes).zfill(2)
        return string

    def predict_duration(self, reg):
        if self.distance is not None and self.uphill is not None:
            seconds = reg.intercept\
                + self.distance * reg.coef_distance\
                + self.uphill * reg.coef_uphill
            self.duration = datetime.timedelta(seconds=seconds)
            self.save()


class LinRegModel(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fitted = models.BooleanField(default=False)
    intercept = models.FloatField(default=0)
    coef_distance = models.FloatField(default=0)
    coef_uphill = models.FloatField(default=0)

    def __str__(self):
        return "ApiKey<%s>" % (self.user.username)


class ApiKey(models.Model):

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    key = models.CharField(max_length=32)

    def __str__(self):
        return "ApiKey<%s>" % (self.user.username)
