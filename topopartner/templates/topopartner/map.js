{% for category in mapdata.categories %}
WAYPOINT_CATEGORY_COLORS["{{ category.id }}"] = "{{ category.color }}";
{% endfor %}
var mapWrapper = new MapWrapper();
mapWrapper.defaultView.center.latitude = {{ mapdata.center.lat }};
mapWrapper.defaultView.center.longitude = {{ mapdata.center.lng }};
{% if not mapdata.track %}
mapWrapper.defaultView.bounds.southwest = {{ mapdata.bounds.sw }};
mapWrapper.defaultView.bounds.northeast = {{ mapdata.bounds.ne }};
{% endif %}
mapWrapper.createLeafletMap("map");
{% if mapdata.edit == 'marker' %}
mapWrapper.appendAddMarkerControl();
{% endif %}
{% if mapdata.edit == 'polyline' %}
mapWrapper.appendAddPolylineControl();
{% endif %}

{% for waypoint in mapdata.waypoints %}
var wpt_{{ waypoint.id }} = new Waypoint(mapWrapper);
wpt_{{ waypoint.id }}.setData({{ waypoint.id }}, {{ waypoint.latitude }}, {{ waypoint.longitude }}, "{{ waypoint.label }}", {% if waypoint.comment %}"{{ waypoint.comment }}"{% else %}null{% endif %}, {% if waypoint.elevation %}{{ waypoint.elevation }}{% else %}null{% endif %}, {% if waypoint.category %}"{{ waypoint.category.id }}"{% else %}null{% endif %}, {% if waypoint.visited %}true{% else %}false{% endif %});
wpt_{{ waypoint.id }}.createLeafletMarker({% if mapdata.edit == 'marker' %}true{% else %}false{% endif %});
{% endfor %}

{% if mapdata.track %}
var trackWrapper = new Track(mapWrapper);
trackWrapper.latlngs = [{% for lat, lon in mapdata.track %}[{{ lat }}, {{ lon }}]{% if forloop.last %}{% else %}, {% endif %}{% endfor %}];
trackWrapper.createLeafletPolyline({% if mapdata.edit == 'polyline' %}true{% else %}false{% endif %}, true);
mapWrapper.leaflet.fitBounds(trackWrapper.leaflet.getBounds());
{% endif %}

setTimeout(function(){ mapWrapper.leaflet.invalidateSize()}, 400);
