
# OMERO Vitessce

An experimental OMERO.web plugin to open OMERO.table data in Vitessce.

*NB: work in progress...*


# Dev install

This app is a plugin of OMERO.web and needs to be installed in the same environment.

    $ cd omero-vitessce
    $ pip install -e .

    $ omero config append omero.web.apps '"omero_vitessce"'

    # Then restart your omero-web server

To open a OMERO table using File ID, go to:

    your-omero-server/vitessce/table/{FILE_ID}
