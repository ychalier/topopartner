from django.urls import path
from . import views

app_name = "topopartner"

urlpatterns = [
    path("", views.view_landing, name="landing"),
    path("about", views.view_about, name="about"),
    path("routes", views.view_routes, name="routes"),
    path("recordings", views.view_recordings, name="recordings"),
    path("track/create", views.view_create_track, name="create_track"),
    path("track/upload", views.view_upload_track, name="upload_track"),
    path("track/<tid>", views.view_track, name="view_track"),
    path("track/<tid>/edit", views.view_edit_track, name="edit_track"),
    path("track/<tid>/elevate", views.view_elevate_track, name="elevate_track"),
    path("track/<tid>/smooth", views.view_smooth_track, name="smooth_track"),
    path("track/<tid>/download", views.view_download_track, name="download_track"),
    path("track/<tid>/download/gpx", views.view_download_track_gpx, name="download_track_gpx"),
    path("track/<tid>/download/stl", views.view_download_track_stl, name="download_track_stl"),
    path("track/<tid>/delete", views.view_delete_track, name="delete_track"),
    path("track/<tid>/points", views.view_track_points, name="track_points"),
    path("fit", views.view_fit, name="fit"),
    path("api/route/list", views.api_list_routes, name="api_list_routes"),
    path("api/route/get", views.api_get_route, name="api_get_route"),
    path("api/recording/post", views.api_post_recording, name="api_post_recording"),
]
