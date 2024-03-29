import datetime
import json
import os
import tempfile

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from django.http import Http404
from django.template.defaultfilters import slugify
from django.contrib.auth.decorators import permission_required
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import PermissionDenied
from django.core.exceptions import SuspiciousOperation
import gpxpy.gpx

from . import models
from . import utils


# ----------------------------------------------- #
# UTILITIES                                       #
# ----------------------------------------------- #


def get_track_from_tid(tid, required_user=None, allow_public=False):
    if not models.Track.objects.filter(id=tid).exists():
        raise Http404("Track does not exist")
    track = models.Track.objects.get(id=tid)
    if not allow_public and (required_user is not None and track.user != required_user):
        raise PermissionDenied
    return track


@permission_required("topopartner.add_track")
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
    if data["is_route"]:
        track.is_route = True
        track.is_recording = False
    else:
        track.is_route = False
        track.is_recording = True
    track.save()
    return HttpResponse(
        reverse("topopartner:view_track", kwargs={"tid": track.id}),
        content_type="text/plain"
    )


def check_api_key(request):
    key = request.GET.get("k")
    if models.ApiKey.objects.filter(key=key).exists():
        return models.ApiKey.objects.get(key=key).user
    raise PermissionDenied


# ----------------------------------------------- #
# VIEWS                                           #
# ----------------------------------------------- #


def view_landing(request):
    return redirect("topopartner:about")


def view_about(request):
    return render(request, "topopartner/about.html", {})


@permission_required("topopartner.view_track")
def view_routes(request):
    """Summary of the existing tracks.
    """
    routes = models.Track.objects\
        .filter(is_route=True, user=request.user)\
        .order_by("-date_added")
    return render(request, "topopartner/routes.html", {
        "routes": routes,
        "api_key": getattr(request.user, "apikey", None),
        "active": "routes"
    })


@permission_required("topopartner.view_track")
def view_recordings(request):
    """Summary of the existing tracks.
    """
    recordings = models.Track.objects\
        .filter(is_recording=True, user=request.user)\
        .order_by("-date_visited")
    linreg, _ = models.LinRegModel.objects.get_or_create(user=request.user)
    return render(request, "topopartner/recordings.html", {
        "recordings": recordings,
        "linreg": linreg,
        "api_key": getattr(request.user, "apikey", None),
        "active": "recordings"
    })


@permission_required("topopartner.add_track")
def view_create_track(request):
    """Create a track.
    """
    if request.method == "POST":
        return create_or_update_track(request)
    mapdata = utils.gather_map_data(request)
    mapdata["edit"] = "polyline"
    return render(request, "topopartner/create_track.html", {
        "mapdata": mapdata,
    })


@permission_required("topopartner.add_track")
def view_upload_track(request):
    """Upload a GPX.
    """
    if request.method != "POST":
        return render(request, "topopartner/upload.html", {})
    if "label" not in request.POST or request.POST["label"].strip() == "":
        return HttpResponse("No label found.", content_type="text/plain")
    if "gpx" not in request.FILES:
        return HttpResponse("No GPX uploaded.", content_type="text/plain")
    is_route = "route" in request.POST
    is_recording = not is_route
    track = models.Track.objects.create(
        user=request.user,
        label=request.POST["label"],
        comment=request.POST.get("comment"),
        gpx=request.FILES["gpx"].read().decode(),
        is_route=is_route,
        is_recording=is_recording,
        date_visited=request.POST.get("visited"),
    )
    if is_recording:
        utils.compute_stats(track, save_values=True)
    return redirect("topopartner:view_track", tid=track.id)


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
        "active": "routes" if track.is_route else "recordings"
    })


@permission_required("topopartner.change_track")
def view_edit_track(request, tid):
    """Edit a track.
    """
    if request.method == "POST":
        return create_or_update_track(request, tid)
    track = get_track_from_tid(tid, required_user=request.user)
    mapdata = utils.gather_map_data(request)
    if track.is_route:
        mapdata["edit"] = "polyline"
    mapdata["track"] = list()
    for track_point in track.iter_trackpoints():
        mapdata["track"].append([track_point.latitude, track_point.longitude])
    return render(request, "topopartner/edit_track.html", {
        "track": track,
        "mapdata": mapdata,
    })


@permission_required("topopartner.change_track")
def view_elevate_track(request, tid):
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


@permission_required("topopartner.change_track")
def view_smooth_track(request, tid):
    """Fetch the elevation data of a track and compute its stats afterwards.
    """
    if request.method == "POST":
        track = get_track_from_tid(tid, required_user=request.user)
        points = utils.clean(
            list(track.iter_trackpoints()),
            float(request.POST.get("smoothing", 8)),
            float(request.POST.get("simplification", .6))
        )
        gpx = gpxpy.gpx.GPX()
        trk = gpxpy.gpx.GPXTrack()
        gpx.tracks.append(trk)
        trkseg = gpxpy.gpx.GPXTrackSegment()
        trk.segments.append(trkseg)
        for point in points:
            trkseg.points.append(point)
        smooth_track = models.Track.objects.create(
            user=request.user,
            label="[SMOOTH] " + track.label,
            comment=track.comment,
            gpx=gpx.to_xml(),
            is_route=track.is_route,
            is_recording=track.is_recording,
            date_visited=track.date_visited,
        )
        utils.compute_stats(smooth_track, save_values=True)
        return redirect("topopartner:view_track", tid=smooth_track.id)
    return redirect("topopartner:view_track", tid=tid)


def view_download_track(request, tid):
    return redirect("topopartner:download_track_gpx")


def view_download_track_gpx(request, tid):
    """Return the GPX of a track as an attachment.
    """
    track = get_track_from_tid(tid, required_user=request.user, allow_public=True)
    response = HttpResponse(track.gpx, content_type="application/gpx+xml")
    response["Content-Disposition"] =\
        'attachment; filename="%s.gpx"' % slugify(track.label)
    return response


def view_download_track_stl(request, tid):
    track = get_track_from_tid(tid, required_user=request.user, allow_public=True)
    gpx = gpxpy.parse(track.gpx)
    mesh = utils.threed_profile(gpx)
    mesh_filename = os.path.join(tempfile.gettempdir(), slugify(track.label) + ".stl")
    mesh.save(mesh_filename)
    with open(mesh_filename, "rb") as file:
        mesh_data = file.read()
    os.remove(mesh_filename)
    response = HttpResponse(mesh_data, content_type="model/stl")
    response["Content-Disposition"] = f'attachment; filename="{slugify(track.label)}.stl"'
    return response


@permission_required("topopartner.delete_track")
def view_delete_track(request, tid):
    """Delete a track.
    """
    track = get_track_from_tid(tid, required_user=request.user)
    is_route = track.is_route
    track.delete()
    if is_route:
        return redirect("topopartner:routes")
    return redirect("topopartner:recordings")


@permission_required("topopartner.view_track")
def view_track_points(request, tid):
    track = get_track_from_tid(tid, required_user=request.user)
    data = [[trkpt.latitude, trkpt.longitude] for trkpt in track.iter_trackpoints()]
    return HttpResponse(json.dumps(data), content_type="application/json")


@permission_required("topopartner.change_linregmodel")
def view_fit(request):
    """Fit the linear regression model.
    """
    linreg, _ = models.LinRegModel.objects.get_or_create(user=request.user)
    if models.Track.objects.filter(is_recording=True, user=request.user).exists():
        reg = utils.linear_regression(models.Track.objects.filter(is_recording=True, user=request.user))
        linreg.coef_distance = reg[0]
        linreg.coef_uphill = reg[1]
        linreg.intercept = reg[2]
        linreg.save()
        for track in models.Track.objects.filter(is_route=True, user=request.user):
            track.predict_duration(linreg)
    return redirect("topopartner:recordings")


# ----------------------------------------------- #
# API                                             #
# ----------------------------------------------- #


def api_list_routes(request):
    user = check_api_key(request)
    routes = models.Track.objects\
        .filter(is_route=True, user=user)\
        .order_by("-date_added")
    data = {"routes": []}
    for route in routes:
        data["routes"].append({
            "label": route.label,
            "tid": route.id,
            "date_added": route.date_added.isoformat(),
            "date_modified": route.date_modified.isoformat(),
            "distance": route.distance,
            "uphill": route.uphill,
            "gpx": route.gpx,
        })
    return HttpResponse(json.dumps(data), content_type="application/json")


def api_get_route(request):
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
        is_route=False,
        is_recording=True,
        date_visited=datetime.datetime.fromisoformat(data["date_visited"]).date(),
    )
    try:
        utils.compute_stats(track, save_values=True)
    except gpxpy.gpx.GPXXMLSyntaxException:
        track.delete()
        raise SuspiciousOperation("Invalid GPX.")
    return HttpResponse("", content_type="text/plain")