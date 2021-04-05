
# OMERO Vitessce

An experimental OMERO.web plugin to open OMERO.table data in Vitessce.

*NB: work in progress...*

## Initial proof of concept

In this workflow, we start by opening an OMERO.table using it's File ID:
```
your-omero-server/vitessce/table/{FILE_ID}
```

This shows the column names and first few rows of the table.
Two `select` inputs allow you to choose 2 Number columns. Clicking `Plot Vitessce`
launches Vitessce in the iframe below, passing it a config that loads the data
from the 2 chosen columns, in the Vitessce `cells.json` format:

<img src="https://user-images.githubusercontent.com/900055/113628918-899fac80-965d-11eb-8e7e-fdc2eaff93ba.png"/>


# Dev install

This app is a plugin of OMERO.web and needs to be installed in the same environment.

    $ cd omero-vitessce
    $ pip install -e .

    $ omero config append omero.web.apps '"omero_vitessce"'

    # Then restart your omero-web server

To open a OMERO table using File ID, go to:

    your-omero-server/vitessce/table/{FILE_ID}
