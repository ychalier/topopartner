from django.urls import path
from . import views

app_name = "topopartner"

urlpatterns = [
    path("tracks", views.view_tracks, name="tracks"),
    path("itineraries", views.tracks_itineraries, name="itineraries"),
    path("recordings", views.tracks_recordings, name="recordings"),
    path("waypoints", views.waypoints, name="waypoints"),
    path("create-track", views.create_track, name="create_track"),
    path("track/<tid>", views.view_track, name="view_track"),
    path("track/<tid>/delete", views.delete_track, name="delete_track"),
    path("track/<tid>/gpx", views.download_gpx, name="gpx"),
    path("track/<tid>/edit", views.edit_track, name="edit_track"),
    path("track/<tid>/elevation", views.fetch_elevation_data, name="fetch_elevation_data"),
    path("track/<tid>/trackpoints", views.get_trackpoints, name="get_trackpoints"),
    path("track/<tid>/create-smooth", views.create_smooth_track, name="create_smooth_track"),
    path("upload", views.upload_track, name="upload_track"),
    path("fit", views.fit_linreg, name="fit_linreg"),
    path("api/itinerary/list", views.api_list_itineraries, name="api_list_itineraries"),
    path("api/itinerary/get", views.api_get_itinerary, name="api_get_itinerary"),
    path("api/recording/post", views.api_post_recording, name="api_post_recording"),
    path("", views.home, name="home"),
]
