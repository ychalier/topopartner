/*****************************************************************************

Interface between the Leaflet objects and Django data.

Here is Leaflet's documentation:
https://leafletjs.com/reference-1.6.0.html

******************************************************************************/

var WAYPOINT_CATEGORY_COLORS = {};
var TRACK_COLOR = "rgba(200, 0, 15, .8)";


// Leaflet.Editable necessity
L.EditControl = L.Control.extend({
    options: {
        position: 'topleft',
        callback: null,
        kind: "",
        html: ""
    },
    onAdd: function(map) {
        var container = L.DomUtil.create('div', 'leaflet-control leaflet-bar');
        var link = L.DomUtil.create('a', '', container);
        link.href = '#';
        link.title = 'Create a new ' + this.options.kind;
        link.innerHTML = this.options.html;
        L.DomEvent.on(link, 'click', L.DomEvent.stop)
            .on(link, 'click', function() {
                window.LAYER = this.options.callback.call(map.editTools);
            }, this);
        return container;
    }
});


var HOME_SVG = `
<svg
    id="i-home"
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 32 32"
    width="16"
    height="16"
    fill="none"
    stroke="black"
    stroke-linecap="round"
    stroke-linejoin="round"
    stroke-width="2">
    <path d="M12 20 L12 30 4 30 4 12 16 2 28 12 28 30 20 30 20 20 Z" />
</svg>
`;


var ROUTE_SVG = `
<svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    width="16"
    height="16">
    <path fill="black" d="M21,8c-1.45,0-2.26,1.44-1.93,2.51l-3.55,3.56c-0.3-0.09-0.74-0.09-1.04,0l-2.55-2.55C12.27,10.45,11.46,9,10,9 c-1.45,0-2.27,1.44-1.93,2.52l-4.56,4.55C2.44,15.74,1,16.55,1,18c0,1.1,0.9,2,2,2c1.45,0,2.26-1.44,1.93-2.51l4.55-4.56 c0.3,0.09,0.74,0.09,1.04,0l2.55,2.55C12.73,16.55,13.54,18,15,18c1.45,0,2.27-1.44,1.93-2.52l3.56-3.55 C21.56,12.26,23,11.45,23,10C23,8.9,22.1,8,21,8z"/>
</svg>
`;


var MARKER_SVG = `
<svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 32 32"
    width="16"
    height="16"
    stroke="black"
    stroke-linecap="round"
    stroke-linejoin="round"
    stroke-width="2">
    <path
        d="M24 15 C21 22 16 30 16 30 16 30 11 22 8 15 5 8 10 2 16 2 22 2 27 8 24 15 Z"
    />
    <circle fill="white" cx="16" cy="11" r="4" />
</svg>
`;


class MapWrapper {
    constructor() {
        this.defaultView = {
            center: {
                latitude: null,
                longitude: null
            },
            zoom: null,
            bounds: {
                southwest: null,
                northeast: null
            }
        }
        this.externalElements = {
            buttonSaveWaypoints: null,
            buttonClearTrack: null,
            buttonSaveTrack: null,
            trackForm: null,
        };
        this.leaflet = null;
        this.track = null;
        this.waypoints = [];
    }

    createLeafletMap(elementId) {
        this.leaflet = L.map(
            elementId, {
                center: [
                    this.defaultView.center.latitude,
                    this.defaultView.center.longitude
                ],
                zoom: (this.defaultView.zoom ? this.defaultView.zoom : 10),
                zoomControl: true,
                preferCanvas: false,
                editable: true,
            }
        );
        L.control.scale().addTo(this.leaflet);
        L.tileLayer(
            "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png", {
                maxNativeZoom: 17,
                maxZoom: 17,
                minZoom: 5,
                noWrap: false,
                opacity: 1,
            }
        ).addTo(this.leaflet);
        if (this.defaultView.bounds.southwest &&
            this.defaultView.bounds.northeast) {
            this.leaflet.fitBounds([
                this.defaultView.bounds.southwest,
                this.defaultView.bounds.northeast
            ], {});
        }
        var self = this;
        L.ResetViewControl = L.Control.extend({
            options: {
                position: "topleft",
            },
            onAdd: (map) => {
                var container = L.DomUtil.create('div', 'leaflet-control leaflet-bar');
                var link = L.DomUtil.create('a', '', container);
                link.href = '#';
                link.title = "Reset view";
                link.innerHTML = HOME_SVG;
                L.DomEvent.on(link, 'click', L.DomEvent.stop)
                    .on(link, 'click', (event) => {
                        self.resetView();
                    }, this);
                return container;
            }
        });
        this.leaflet.addControl(new L.ResetViewControl());
    }

    resetView() {
        if (this.track) {
            this.leaflet.fitBounds(this.track.leaflet.getBounds());
        } else {
            this.leaflet.fitBounds([this.defaultView.bounds.southwest, this.defaultView.bounds.northeast]);
        }
    }

    callbackAddMarker(tools) {
        let waypoint = new Waypoint(this);
        waypoint.data.label = "New Marker";
        waypoint.leaflet = this.leaflet.editTools.startMarker(tools);
        waypoint.leaflet.addEventListener("add", (event) => {
            waypoint.data.latitude = waypoint.leaflet._latlng.lat;
            waypoint.data.longitude = waypoint.leaflet._latlng.lng;
            waypoint.setChanged();
            waypoint.updateView();
        });
        waypoint.init(true);
    }

    callbackAddPolyline(tools) {
        if (this.track) {
            return;
        }
        let track = new Track(this);
        track.leaflet = this.leaflet.editTools.startPolyline(tools);
        track.leaflet.setStyle({
            color: TRACK_COLOR,
        });
        track.init();
        track.edited = true;
    }

    appendAddMarkerControl() {
        var self = this;
        L.NewMarkerControl = L.EditControl.extend({
            options: {
                position: 'topleft',
                callback: (tools) => {
                    self.callbackAddMarker(tools);
                },
                kind: 'marker',
                html: MARKER_SVG
            }
        });
        this.leaflet.addControl(new L.NewMarkerControl());
    }

    appendAddPolylineControl() {
        var self = this;
        L.NewLineControl = L.EditControl.extend({
            options: {
                position: 'topleft',
                callback: (tools) => {
                    self.callbackAddPolyline(tools);
                },
                kind: 'line',
                html: ROUTE_SVG
            }
        });
        this.leaflet.doubleClickZoom.disable();
        this.leaflet.addControl(new L.NewLineControl());
        this.leaflet.on(
            'editable:vertex:ctrlclick editable:vertex:metakeyclick',
            function(event) {
                event.vertex.continue();
            });
    }

    bindButtonSaveWaypoits(elementId) {
        var self = this;
        this.externalElements.buttonSaveWaypoints =
            document.getElementById("buttonSaveChanges");
        this.externalElements.buttonSaveWaypoints.addEventListener("click", (event) => {
            let changed = [];
            for (let i = 0; i < self.waypoints.length; i++) {
                if (self.waypoints[i].status.changed) {
                    changed.push(self.waypoints[i].toJson());
                }
            }
            let url = "";
            let xhr = new XMLHttpRequest();
            xhr.open("POST", url, true);
            xhr.setRequestHeader("Content-Type", "application/json");
            xhr.setRequestHeader("X-CSRFToken", CSRF_TOKEN);
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4 && xhr.status === 200) {
                    document.location.reload(true);
                }
            };
            let data = JSON.stringify(changed);
            xhr.send(data);
        });
    }

    bindTrackForm(elementId) {
        this.externalElements.trackForm = document.getElementById(elementId);
    }

    bindButtonClearTrack(elementId) {
        this.externalElements.buttonClearTrack =
            document.getElementById(elementId);
        var self = this;
        this.externalElements.buttonClearTrack.addEventListener("click", (event) => {
            if (self.track) {
                self.track.leaflet.remove();
                delete self.track;
                self.track = null;
            } else {
                alert("There is no track to clear.");
            }
        });
    }

    bindButtonSaveTrack(elementId) {
        this.externalElements.buttonSaveTrack =
            document.getElementById(elementId);
        var self = this;
        this.externalElements.buttonSaveTrack.addEventListener("click", (event) => {
            if (self.track) {
                self.track.save();
            } else {
                alert("There is no track to save.");
            }
        });
    }

}


class Track {
    constructor(mapWrapper) {
        this.map = mapWrapper;
        this.latlngs = null;
        this.leaflet = null;
        this.highlighter = null;
        this.edited = false;
    }

    createLeafletPolyline(editable, createHighlighter) {
        this.leaflet = L.polyline(this.latlngs, {
            color: TRACK_COLOR,
        }).addTo(this.map.leaflet);
        if (createHighlighter) {
            this.highlighter = L.marker([0, 0]).addTo(this.map.leaflet);
            let highlighterIcon = L.divIcon({
                className: "polyline_marker",
                iconAnchor: [10, 10],
                labelAnchor: [-6, 0],
                popupAnchor: [0, -36],
                html: `
                <svg
                    class="polyline_marker_icon"
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="-10 -10 20 20"
                    width="20"
                    height="20"
                    fill="transparent"
                    stroke="black"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2">
                    <circle fill="white" cx="0" cy="0" r="4" />
                </svg>
                `
            });
            this.highlighter.setIcon(highlighterIcon);
        }
        if (editable) {
            this.leaflet.enableEdit();
            this.leaflet.addEventListener("editable:editing ", (event) => {
                this.edited = true;
            });
        }
        this.init();
    }

    init() {
        this.map.track = this;
    }

    save() {
        let label = this.map.externalElements.trackForm
            .querySelector("input[name='label']").value;
        let comment = this.map.externalElements.trackForm
            .querySelector("textarea[name='comment']").value;
        let is_public = this.map.externalElements.trackForm
            .querySelector("input[name='public']").checked;
        let is_itinerary = this.map.externalElements.trackForm
            .querySelector("input[name='itinerary']").checked;
        if (label) {
            let latlngs = [];
            if (this.edited) {
                for (let i = 0; i < this.leaflet._latlngs.length; i++) {
                    latlngs.push({
                        lat: this.leaflet._latlngs[i].lat,
                        lng: this.leaflet._latlngs[i].lng
                    });
                }
            }
            let data = JSON.stringify({
                label: label,
                comment: comment,
                is_public: is_public,
                is_itinerary: is_itinerary,
                latlngs: latlngs,
                edited: this.edited
            });
            let url = "";
            let xhr = new XMLHttpRequest();
            xhr.open("POST", url, true);
            xhr.setRequestHeader("Content-Type", "application/json");
            xhr.setRequestHeader("X-CSRFToken", CSRF_TOKEN);
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4 && xhr.status === 200) {
                    let redirectUrl = xhr.responseText;
                    window.location.href = redirectUrl;
                }
            };
            xhr.send(data);
        } else {
            alert("You must specify a label!");
        }
    }

}


class Waypoint {
    constructor(mapWrapper) {
        this.map = mapWrapper;
        this.status = {
            changed: false,
            delete: false,
        };
        this.data = {
            mid: null,
            latitude: null,
            longitude: null,
            label: null,
            elevation: null,
            comment: null,
            category: null,
            visited: null,
        }
        this.tooltip = null;
        this.leaflet = null;
    }

    setData(mid, lat, lng, lbl, cmt, ele, cat, vis) {
        this.data.mid = mid;
        this.data.latitude = lat;
        this.data.longitude = lng;
        this.data.label = lbl;
        this.data.comment = cmt;
        this.data.elevation = ele;
        this.data.category = cat;
        this.data.visited = vis;
    }

    setChanged() {
        if (!this.status.changed) {
            this.status.changed = true;
            if (this.map.externalElements.buttonSaveWaypoints) {
                this.map.externalElements.buttonSaveWaypoints
                    .removeAttribute("disabled");
            }
        }
    }

    setDataAttribute(attr, value, formatter) {
        let formattedValue = formatter ? formatter(value) : value;
        if (formattedValue != null && formattedValue != this.data[attr]) {
            this.data[attr] = formattedValue;
            this.setChanged();
        }
    }

    popupSaveCallback(event) {
        let p = event.target.parentNode;
        this.setDataAttribute("label",
            p.querySelector("input[name='label']").value);
        this.setDataAttribute("comment",
            p.querySelector("input[name='comment']").value);
        this.setDataAttribute("elevation",
            p.querySelector("input[name='elevation']").value, (elevation) => {
                if (elevation) {
                    return parseFloat(elevation);
                }
                return null;
            });
        this.setDataAttribute("category",
            p.querySelector("select[name='category']").value);
        this.setDataAttribute("visited",
            p.querySelector("input[name='visited']").checked);
        this.updateView();
    }

    popupDeleteCallback(event) {
        this.status.delete = true;
        this.leaflet.remove();
        this.setChanged();
    }

    setPopup() {
        var self = this;
        let template = document.getElementById("template_marker_popup").content;
        let container = document.createElement("div");
        container.appendChild(document.importNode(template, true));
        container.querySelector("input[name='label']").value = this.data.label;
        if (this.data.comment) {
            container.querySelector("input[name='comment']").value =
                this.data.comment;
        }
        if (this.data.elevation) {
            container.querySelector("input[name='elevation']").value =
                this.data.elevation;
        }
        if (this.data.category) {
            let select = container.querySelector("select[name='category']");
            select.value = this.data.category;
        }
        if (this.data.visited) {
            container.querySelector("input[name='visited']").checked = true;
        }
        container.querySelector("input[name='label']").addEventListener("change", (event) => {
            self.popupSaveCallback(event);
        });
        container.querySelector("input[name='comment']").addEventListener("change", (event) => {
            self.popupSaveCallback(event);
        });
        container.querySelector("input[name='elevation']").addEventListener("change", (event) => {
            self.popupSaveCallback(event);
        });
        container.querySelector("select[name='category']").addEventListener("change", (event) => {
            self.popupSaveCallback(event);
        });
        container.querySelector("input[name='visited']").addEventListener("change", (event) => {
            self.popupSaveCallback(event);
        });
        container.querySelector("button[name='delete']").addEventListener("click",
            (event) => {
                self.popupDeleteCallback(event);
            });
        this.leaflet.bindPopup(container);
    }

    updateViewTooltip() {
        let string = "<p>";
        if (this.status.changed) {
            string += "*";
        }
        string += "<b>" + this.data.label + "</b>";
        if (this.data.elevation != null) {
            string += " (" + Math.round(this.data.elevation) + "m)";
        }
        string += "</p>";
        if (this.data.comment != null) {
            string += "<p>" + this.data.comment + "</p>";
        }
        if (this.tooltip == null) {
            this.tooltip = this.leaflet.bindTooltip(string, {
                "sticky": false
            });
        } else {
            this.tooltip.setTooltipContent(string);
        }
    }

    updateViewIcon() {
        let backgroundColor = "#430c7a";
        if (this.data.category != null &&
            this.data.category in WAYPOINT_CATEGORY_COLORS) {
            backgroundColor = WAYPOINT_CATEGORY_COLORS[this.data.category];
        }
        let strokeWidth = 1;
        if (this.data.visited) {
            strokeWidth = 2;
        }
        let html = `
        <svg
            class="marker_icon"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 32 32"
            width="32"
            height="32"
            fill="transparent"
            stroke="black"
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="${strokeWidth}">
            <path
                fill="${backgroundColor}"
                d="M24 15 C21 22 16 30 16 30 16 30 11 22 8 15 5 8 10 2 16 2 22 2 27 8 24 15 Z"
            />
            <circle fill="white" cx="16" cy="11" r="4" />
        </svg>
        `;
        let icon = L.divIcon({
            className: "marker_wrapper",
            iconAnchor: [0, 0],
            labelAnchor: [-6, 0],
            popupAnchor: [0, -36],
            html: html,
        })
        this.leaflet.setIcon(icon);
    }

    updateView() {
        this.updateViewTooltip();
        this.updateViewIcon();
    }

    createLeafletMarker(editable) {
        this.leaflet = L.marker(
            [this.data.latitude, this.data.longitude], {
                draggable: editable
            }
        );
        this.leaflet.addTo(this.map.leaflet);
        this.init(editable);
    }

    init(editable) {
        var self = this;
        this.leaflet.on("dragend", (event) => {
            if (event.target._latlng.lat != self.data.latitude ||
                event.target._latlng.lng != self.data.longitude) {
                self.setChanged();
                self.updateView();
            }
            self.data.latitude = event.target._latlng.lat;
            self.data.longitude = event.target._latlng.lng;
        });
        if (editable) {
            this.setPopup();
        }
        this.updateView();
        this.map.waypoints.push(this);
    }

    toJson() {
        return {
            status: this.status,
            data: this.data,
        }
    }

}

window.addEventListener("load", () => {
    document.querySelectorAll(".still-map").forEach((item) => {
        let elementId = item.getAttribute("id");
        let data = item.getAttribute("data").slice(0, -1).split(";").map(s => s.split(",").map(x => parseFloat(x)));
        let center = [0, 0];
        data.forEach((pt) => {
            center[0] += pt[0];
            center[1] += pt[1];
        });
        center[0] /= data.length;
        center[1] /= data.length;
        let leaflet = L.map(
            elementId, {
                center: center,
                zoom: 10,
                zoomControl: false,
                scrollWheelZoom: false,
            }
        );
        leaflet.dragging.disable();
        L.tileLayer(
            "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png", {
                maxNativeZoom: 17,
                maxZoom: 17,
                minZoom: 5,
                noWrap: false,
                opacity: 1,
            }
        ).addTo(leaflet);
        let polyline = L.polyline(data, {
            color: TRACK_COLOR,
        }).addTo(leaflet);
        leaflet.fitBounds(polyline.getBounds());
    });
});