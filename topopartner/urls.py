from django.urls import path
from . import views

app_name = "topopartner"

urlpatterns = [
    path("itineraries", views.tracks_itineraries, name="itineraries"),
    path("recordings", views.tracks_recordings, name="recordings"),
    path("waypoints", views.waypoints, name="waypoints"),
    path("create-track", views.create_track, name="create_track"),
    path("track/<tid>", views.view_track, name="view_track"),
    path("track/<tid>/delete", views.delete_track, name="delete_track"),
    path("track/<tid>/gpx", views.download_gpx, name="gpx"),
    path("track/<tid>/edit", views.edit_track, name="edit_track"),
    path("track/<tid>/elevation", views.fetch_elevation_data, name="fetch_elevation_data"),
    path("upload", views.upload_track, name="upload_track"),
    path("fit", views.fit_linreg, name="fit_linreg"),
    path("chaine-des-puys", views.chaine_des_puys, name="chaine_des_puys"),
    path("", views.home, name="home"),
]
