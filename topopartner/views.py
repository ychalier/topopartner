# pylint: disable=C0114,E0401,E0611,E1101,C0103
import json
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from django.http import Http404
from django.template.defaultfilters import slugify
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import PermissionDenied
from django.core.exceptions import SuspiciousOperation
from piweb.decorators import require_app_access
import dateutil.parser
import gpxpy.gpx
from . import models
from . import utils


def home(request):
    """Purpose is yet to be defined.
    """
    return render(request, "topopartner/home.html", {})


def get_track_from_tid(tid, required_user=None, allow_public=False):
    if not models.Track.objects.filter(id=tid).exists():
        raise Http404("Track does not exist")
    track = models.Track.objects.get(id=tid)
    if not allow_public and (required_user is not None and track.user != required_user):
        raise PermissionDenied
    return track


@require_app_access("topopartner")
def waypoints(request):
    """View of the waypoints in the database.
    """
    if request.method == "POST":
        return create_or_update_waypoint(request)
    data = utils.gather_map_data(request)
    data["edit"] = "marker"
    return render(request, "topopartner/waypoints.html", {
        "mapdata": data,
    })


@require_app_access("topopartner")
def create_or_update_waypoint(request):
    """Parse the POST body content (expecting a JSON) to update the waypoints
    in the database.
    """
    for item in json.loads(request.body.decode("utf-8")):
        if models.Waypoint.objects.filter(id=item["data"]["mid"], user=request.user).exists():
            waypoint = models.Waypoint.objects.get(id=item["data"]["mid"], user=request.user)
        else:
            waypoint = models.Waypoint.objects.create(label="", latitude=0, longitude=0, user=request.user)
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
            and models.WaypointCategory.objects.filter(id=int(item["data"]["category"]), user=request.user).exists():
            category = models.WaypointCategory.objects.get(id=int(item["data"]["category"]), user=request.user)
            waypoint.category = category
        else:
            waypoint.category = None
        waypoint.save()
    return HttpResponse(reverse("topopartner:waypoints"), content_type="text/plain")

@require_app_access("topopartner")
def view_tracks(request):
    """Summary of the existing tracks.
    """
    itineraries = models.Track.objects\
        .filter(is_itinerary=True, user=request.user)\
        .order_by("-date_added")
    recordings = models.Track.objects\
        .filter(is_recording=True, user=request.user)\
        .order_by("-date_visited")
    linreg, _ = models.LinRegModel.objects.get_or_create(user=request.user)
    api_key = None
    if hasattr(request.user, "apikey"):
        api_key = request.user.apikey
    return render(request, "topopartner/tracks.html", {
        "itineraries": itineraries,
        "recordings": recordings,
        "linreg": linreg,
        "api_key": api_key,
    })


@require_app_access("topopartner")
def tracks_itineraries(request):
    """Summary of the existing tracks.
    """
    itineraries = models.Track.objects\
        .filter(is_itinerary=True, user=request.user)\
        .order_by("-date_added")
    return render(request, "topopartner/tracks_itineraries.html", {
        "itineraries": itineraries,
    })


@require_app_access("topopartner")
def tracks_recordings(request):
    """Summary of the existing tracks.
    """
    recordings = models.Track.objects\
        .filter(is_recording=True, user=request.user)\
        .order_by("-date_visited")
    linreg, _ = models.LinRegModel.objects.get_or_create(user=request.user)
    return render(request, "topopartner/tracks_recordings.html", {
        "recordings": recordings,
        "linreg": linreg
    })


def view_track(request, tid):
    """Simple view for a track.
    """
    track = get_track_from_tid(tid, required_user=request.user, allow_public=True)
    mapdata = utils.gather_map_data(request)
    mapdata["track"] = list()
    for trkpt in track.iter_trackpoints():
        mapdata["track"].append([trkpt.latitude, trkpt.longitude])
    elevation_data = utils.compute_stats(track)
    return render(request, "topopartner/track.html", {
        "track": track,
        "mapdata": mapdata,
        "elevation_data": elevation_data,
    })


@require_app_access("topopartner")
def get_trackpoints(request, tid):
    track = get_track_from_tid(tid, required_user=request.user)
    data = [[trkpt.latitude, trkpt.longitude] for trkpt in track.iter_trackpoints()]
    return HttpResponse(json.dumps(data), content_type="application/json")


@require_app_access("topopartner")
def fetch_elevation_data(request, tid):
    """Fetch the elevation data of a track and compute its stats afterwards.
    """
    track = get_track_from_tid(tid, required_user=request.user)
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
    track = get_track_from_tid(tid, required_user=request.user, allow_public=True)
    response = HttpResponse(track.gpx, content_type="application/gpx+xml")
    response["Content-Disposition"] =\
        'attachment; filename="%s.gpx"' % slugify(track.label)
    return response


@require_app_access("topopartner")
def create_or_update_track(request, tid=None):
    """Parse the POST body content (expecting a JSON) to update the tracks
    in the database.
    """
    data = json.loads(request.body.decode("utf-8"))
    if tid is None:
        track = models.Track.objects.create(label="", gpx="", user=request.user)
    else:
        track = get_track_from_tid(tid, required_user=request.user)
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


@require_app_access("topopartner")
def edit_track(request, tid):
    """Edit a track.
    """
    if request.method == "POST":
        return create_or_update_track(request, tid)
    track = get_track_from_tid(tid, required_user=request.user)
    mapdata = utils.gather_map_data(request)
    if track.is_itinerary:
        mapdata["edit"] = "polyline"
    mapdata["track"] = list()
    for track_point in track.iter_trackpoints():
        mapdata["track"].append([track_point.latitude, track_point.longitude])
    return render(request, "topopartner/edit_track.html", {
        "track": track,
        "mapdata": mapdata,
    })


@require_app_access("topopartner")
def create_track(request):
    """Create a track.
    """
    if request.method == "POST":
        return create_or_update_track(request)
    mapdata = utils.gather_map_data(request)
    mapdata["edit"] = "polyline"
    return render(request, "topopartner/create_track.html", {
        "mapdata": mapdata,
    })


@require_app_access("topopartner")
def delete_track(request, tid):
    """Delete a track.
    """
    track = get_track_from_tid(tid, required_user=request.user)
    is_itinerary = track.is_itinerary
    track.delete()
    if is_itinerary:
        return redirect("topopartner:itineraries")
    return redirect("topopartner:recordings")


@require_app_access("topopartner")
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
        user=request.user,
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


@require_app_access("topopartner")
def fit_linreg(request):
    """Fit the linear regression model.
    """
    linreg, _ = models.LinRegModel.objects.get_or_create(user=request.user)
    if models.Track.objects.filter(is_recording=True, user=request.user).exists():
        reg = utils.linear_regression(models.Track.objects.filter(is_recording=True, user=request.user))
        linreg.coef_distance = reg[0]
        linreg.coef_uphill = reg[1]
        linreg.intercept = reg[2]
        linreg.save()
        for track in models.Track.objects.filter(is_itinerary=True, user=request.user):
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


def check_api_key(request):
    key = request.GET.get("k")
    if models.ApiKey.objects.filter(key=key).exists():
        return models.ApiKey.objects.get(key=key).user
    raise PermissionDenied


def api_list_itineraries(request):
    user = check_api_key(request)
    itineraries = models.Track.objects\
        .filter(is_itinerary=True, user=user)\
        .order_by("-date_added")
    data = {"itineraries": []}
    for itinerary in itineraries:
        data["itineraries"].append({
            "label": itinerary.label,
            "tid": itinerary.id,
            "date_added": itinerary.date_added.isoformat(),
            "date_modified": itinerary.date_modified.isoformat(),
            "distance": itinerary.distance,
            "uphill": itinerary.uphill,
            "gpx": itinerary.gpx,
        })
    return HttpResponse(json.dumps(data), content_type="application/json")


def api_get_itinerary(request):
    user = check_api_key(request)
    tid = request.GET.get("tid")
    if models.Track.objects.filter(id=tid, user=user).exists():
        track = models.Track.objects.get(id=tid, user=user)
        data = {
            "label": track.label,
            "comment": track.comment,
            "date_added": track.date_added.isoformat(),
            "date_modified": track.date_modified.isoformat(),
            "gpx": track.gpx,
            "distance": track.distance,
            "uphill": track.uphill,
        }
        return HttpResponse(json.dumps(data), content_type="application/json")
    raise Http404("Track does not exist.")


@csrf_exempt
def api_post_recording(request):
    user = check_api_key(request)
    try:
        data = json.loads(request.body.decode())
    except json.JSONDecodeError:
        raise SuspiciousOperation("Invalid JSON body.")
    if "label" not in data:
        raise SuspiciousOperation("No label found.")
    if "comment" not in data:
        raise SuspiciousOperation("No comment found.")
    if "gpx" not in data:
        raise SuspiciousOperation("No GPX found.")
    if "date_visited" not in data:
        raise SuspiciousOperation("No date visited found.")
    track = models.Track.objects.create(
        user=user,
        label=data["label"],
        comment=data["comment"],
        gpx=data["gpx"],
        is_itinerary=False,
        is_recording=True,
        date_visited=dateutil.parser.parse(data["date_visited"]),
    )
    try:
        utils.compute_stats(track, save_values=True)
    except gpxpy.gpx.GPXXMLSyntaxException:
        track.delete()
        raise SuspiciousOperation("Invalid GPX.")
    return HttpResponse("", content_type="text/plain")