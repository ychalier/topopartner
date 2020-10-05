# pylint: disable=C0114,E0401,E0611,E1101,C0103
import json
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from django.http import Http404
from django.template.defaultfilters import slugify
from django.contrib.auth.decorators import login_required
from . import models
from . import utils


def home(request):
    """Purpose is yet to be defined.
    """
    return render(request, "topopartner/home.html", {})


@login_required
def waypoints(request):
    """View of the waypoints in the database.
    """
    if request.method == "POST":
        return create_or_update_waypoint(request)
    data = utils.gather_map_data()
    data["edit"] = "marker"
    return render(request, "topopartner/waypoints.html", {
        "mapdata": data,
    })


@login_required
def create_or_update_waypoint(request):
    """Parse the POST body content (expecting a JSON) to update the waypoints
    in the database.
    """
    for item in json.loads(request.body.decode("utf-8")):
        if models.Waypoint.objects.filter(id=item["data"]["mid"]).exists():
            waypoint = models.Waypoint.objects.get(id=item["data"]["mid"])
        else:
            waypoint = models.Waypoint.objects.create(label="", latitude=0, longitude=0)
        if item["status"]["delete"]:
            waypoint.delete()
            continue
        waypoint.label = item["data"]["label"]
        waypoint.latitude = item["data"]["latitude"]
        waypoint.longitude = item["data"]["longitude"]
        waypoint.elevation = item["data"]["elevation"]
        waypoint.comment = item["data"]["comment"]
        waypoint.visited = item["data"]["visited"]
        if item["data"]["category"] is not None\
            and models.WaypointCategory.objects.filter(id=int(item["data"]["category"])):
            category = models.WaypointCategory.objects.get(id=int(item["data"]["category"]))
            waypoint.category = category
        else:
            waypoint.category = None
        waypoint.save()
    return HttpResponse(reverse("topopartner:waypoints"), content_type="text/plain")


@login_required
def tracks_itineraries(request):
    """Summary of the existing tracks.
    """
    itineraries = models.Track.objects\
        .filter(is_itinerary=True)\
        .order_by("-date_added")
    return render(request, "topopartner/tracks_itineraries.html", {
        "itineraries": itineraries,
    })


@login_required
def tracks_recordings(request):
    """Summary of the existing tracks.
    """
    recordings = models.Track.objects\
        .filter(is_recording=True)\
        .order_by("-date_visited")
    linreg = models.LinRegModel.load()
    return render(request, "topopartner/tracks_recordings.html", {
        "recordings": recordings,
        "linreg": linreg
    })


def view_track(request, tid):
    """Simple view for a track.
    """
    if not models.Track.objects.filter(id=tid).exists():
        raise Http404("Track does not exist or is not public.")
    track = models.Track.objects.get(id=tid)
    if not request.user.is_authenticated and not track.public:
        raise Http404("Track does not exist or is not public.")
    mapdata = utils.gather_map_data()
    mapdata["track"] = list()
    for trkpt in track.iter_trackpoints():
        mapdata["track"].append([trkpt.latitude, trkpt.longitude])
    elevation_data = utils.compute_stats(track)
    return render(request, "topopartner/track.html", {
        "track": track,
        "mapdata": mapdata,
        "elevation_data": elevation_data,
    })


@login_required
def fetch_elevation_data(_, tid):
    """Fetch the elevation data of a track and compute its stats afterwards.
    """
    track = models.Track.objects.get(id=tid)
    if not utils.fetch_elevation_data(track):
        return HttpResponse(
            "Could not fetch elevation data. Contact server admin and check the logs.",
            content_type="text/plain"
        )
    utils.compute_stats(track, save_values=True)
    return redirect("topopartner:view_track", tid=track.id)


def download_gpx(request, tid):
    """Return the GPX of a track as an attachment.
    """
    if not models.Track.objects.filter(id=tid).exists():
        raise Http404("Track does not exists!")
    track = models.Track.objects.get(id=tid)
    if not request.user.is_authenticated and not track.public:
        raise Http404("Track does not exist or is not public.")
    response = HttpResponse(track.gpx, content_type="application/gpx+xml")
    response["Content-Disposition"] =\
        'attachment; filename="%s.gpx"' % slugify(track.label)
    return response


@login_required
def create_or_update_track(request, tid=None):
    """Parse the POST body content (expecting a JSON) to update the tracks
    in the database.
    """
    data = json.loads(request.body.decode("utf-8"))
    if tid is None:
        track = models.Track.objects.create(label="", gpx="")
    else:
        track = models.Track.objects.get(id=tid)
    if data["edited"]:
        track.gpx = utils.latlngs_to_gpx(data["latlngs"]).to_xml()
    track.label = data["label"]
    track.comment = data["comment"]
    track.public = data["is_public"]
    if data["is_itinerary"]:
        track.is_itinerary = True
        track.is_recording = False
    else:
        track.is_itinerary = False
        track.is_recording = True
    track.save()
    return HttpResponse(
        reverse("topopartner:view_track", kwargs={"tid": track.id}),
        content_type="text/plain"
    )


@login_required
def edit_track(request, tid):
    """Edit a track.
    """
    if request.method == "POST":
        return create_or_update_track(request, tid)
    track = models.Track.objects.get(id=tid)
    mapdata = utils.gather_map_data()
    if track.is_itinerary:
        mapdata["edit"] = "polyline"
    mapdata["track"] = list()
    for track_point in track.iter_trackpoints():
        mapdata["track"].append([track_point.latitude, track_point.longitude])
    return render(request, "topopartner/edit_track.html", {
        "track": track,
        "mapdata": mapdata,
    })


@login_required
def create_track(request):
    """Create a track.
    """
    if request.method == "POST":
        return create_or_update_track(request)
    mapdata = utils.gather_map_data()
    mapdata["edit"] = "polyline"
    return render(request, "topopartner/create_track.html", {
        "mapdata": mapdata,
    })


@login_required
def delete_track(_, tid):
    """Delete a track.
    """
    if not models.Track.objects.filter(id=tid).exists():
        raise Http404("Track does not exists!")
    track = models.Track.objects.get(id=tid)
    is_itinerary = track.is_itinerary
    track.delete()
    if is_itinerary:
        return redirect("topopartner:itineraries")
    return redirect("topopartner:recordings")


@login_required
def upload_track(request):
    """Upload a GPX.
    """
    if request.method != "POST":
        return render(request, "topopartner/upload.html", {})
    if "label" not in request.POST or request.POST["label"].strip() == "":
        return HttpResponse("No label found.", content_type="text/plain")
    if "gpx" not in request.FILES:
        return HttpResponse("No GPX uploaded.", content_type="text/plain")
    is_itinerary = "itinerary" in request.POST
    is_recording = not is_itinerary
    track = models.Track.objects.create(
        label=request.POST["label"],
        comment=request.POST.get("comment"),
        gpx=request.FILES["gpx"].read().decode(),
        is_itinerary=is_itinerary,
        is_recording=is_recording,
        date_visited=request.POST.get("visited"),
    )
    if is_recording:
        utils.compute_stats(track, save_values=True)
    return redirect("topopartner:view_track", tid=track.id)


@login_required
def fit_linreg(_):
    """Fit the linear regression model.
    """
    linreg = models.LinRegModel.load()
    if models.Track.objects.filter(is_recording=True).exists():
        reg = utils.linear_regression(models.Track.objects.filter(is_recording=True))
        linreg.intercept = reg.intercept_
        linreg.coef_distance = reg.coef_[0]
        linreg.coef_uphill = reg.coef_[1]
        linreg.save()
        for track in models.Track.objects.filter(is_itinerary=True):
            track.predict_duration(linreg)
    return redirect("topopartner:recordings")


def chaine_des_puys(request):
    """Dynamic view for https://github.com/ychalier/chaine-des-puys
    """
    visit_current = 0
    visit_total = 0
    visit_percent = 0
    waypoints_ = list()
    if models.WaypointCategory.objects.filter(name="Chaîne des Puys").exists():
        category = models.WaypointCategory.objects.get(name="Chaîne des Puys")
        waypoints_ = models.Waypoint.objects.filter(category=category).order_by("-latitude")
        for waypoint in waypoints_:
            x, y = utils.latlng_to_xy(waypoint.latitude, waypoint.longitude)
            waypoint.x = x
            waypoint.y = y
            visit_total += 1
            if waypoint.visited:
                visit_current += 1
        visit_percent = 100. * visit_current / visit_total
    return render(request, "topopartner/chaine_des_puys.html", {
        "waypoints": waypoints_,
        "visit_current": visit_current,
        "visit_total": visit_total,
        "visit_percent": visit_percent,
    })
