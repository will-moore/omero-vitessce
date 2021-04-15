
# OMERO Vitessce

An experimental OMERO.web plugin to open OMERO.table data in Vitessce.

*NB: work in progress...*

## Initial proof of concept

This aims to display a scatter plot in Vitessce, with points corresponding to
Polygons displayed on an Image.

You need to have an OMERO.table or CSV file with 2 number columns for the scatter
plot data and a `shape_id` column for the Polygons in OMERO.

If the table also has an `Image` or an `image_id` column, then that Image ID
will be used, or you can choose a different ID or an OME-Zarr URL to load the image.

In this workflow, we start by opening an OMERO.table or CSV using it's File ID:
```
your-omero-server/vitessce/table/{FILE_ID}
```

This shows the column names and first few rows of the table.
Two `select` inputs allow you to choose 2 Number columns.
The Image ID is shown and the corresponding image thumbnail.

Clicking `Open Vitessce` launches Vitessce in the iframe below, with a URL like this
for the screenshot below:

http://vitessce.io/index.html?url=http://omero-server/vitessce/vitessce_config/64805/max/mean/?image=3676

That `omero-server` URL will load a Vitessce config containing URLs for loading the `cells.json` and
the `OME-Zarr` image:

<img src="https://user-images.githubusercontent.com/900055/114845207-7dd98600-9dd3-11eb-822e-33f7a9f5ebc2.png"/>


# Known issues

 - Currently this only works with `public` data in the OMERO server, since Vitescce doesn't
include the OMERO session credentials when loading data from OMERO.

 - When loading Images from OMERO, tiled images are not supported, so the size is limited
 by the maximum plane size that can be loaded from OMERO (e.g. 10k * 12k).

 - The channel controllers are not displayed in Vitessce when loading images from OMERO
 or from a locally-hosted URL, but work OK when loading from s3 (reason unknown)

# Dev install

This app is a plugin of OMERO.web and needs to be installed in the same environment.

    $ cd omero-vitessce
    $ pip install -e .

    $ omero config append omero.web.apps '"omero_vitessce"'

    # Then restart your omero-web server

To open a OMERO table using File ID, go to:

    your-omero-server/vitessce/table/{FILE_ID}
