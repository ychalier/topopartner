# Topopartner

**Topopartner** is a [Django](https://www.djangoproject.com/) application dedicated to topographic personal data management. Namely, it holds a database of **waypoints** and **tracks**. It offers a track edition interface, GPX exports, elevation profile plots, hike duration prediction, and more.

## Getting Started

### Prerequisites

You'll need Python 3.6 or above.

### Installation

1. Install the module from its custom package repository.
    ```bash
    pip install --extra-index-url="https://packages.chalier.fr" django-topopartner
    ```

2. Edit the website `settings.py`:
  - Add `mathfilters` to the `INSTALLED_APPS`
  - Add `topopartner` to the `INSTALLED_APPS`

3. Migrate the database:
    ```bash
    python manage.my migrate
    ```

4. Collect the new static files (override if necessary):
    ```bash
    python manage.my collectstatic
    ```

5. Integrate `topopartner.urls` in your project URLs

## Built With

- [Django](https://www.djangoproject.com/)
- [Leaflet](https://leafletjs.com/)
- [Leaflet.Editable](https://github.com/Leaflet/Leaflet.Editable)
- [gpxpy](https://pypi.org/project/gpxpy/)
- [OpenTopoMap](https://wiki.openstreetmap.org/wiki/OpenTopoMap)
- [GPS Visualizer](https://www.gpsvisualizer.com/)
- [scikit-learn](https://scikit-learn.org/stable/)
- [Material Design Icons](https://material.io/resources/icons/)
- [Bytesize Icons](https://github.com/danklammer/bytesize-icons)

## Future Work Pointers

Here are some other elevation sources that could be implemented in this application:

- [SRTM.py](https://github.com/tkrajina/srtm.py)
- [Open-Elevation](https://github.com/Jorl17/open-elevation)

## Background Image

The contour lines drawn on the [background](topopartner/static/topopartner/img/pattern8.jpg) were generated by randomly placing periodic Gaussians on a 2D plane using [NumPy](https://numpy.org/) and [Matplotlib](https://matplotlib.org/) (and a bit of Photoshop 😄).
