#
# Copyright (c) 2021 University of Dundee.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import pandas as pd
import numpy as np
import tempfile
import zarr
import os
import json
from shapely.geometry import Polygon
from omero_marshal import get_encoder

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.core.urlresolvers import reverse

from omero.model import OriginalFileI
from omero.model.enums import PixelsTypeint8, PixelsTypeuint8, PixelsTypeint16
from omero.model.enums import PixelsTypeuint16, PixelsTypeint32
from omero.model.enums import PixelsTypeuint32, PixelsTypefloat
from omero.model.enums import PixelsTypecomplex, PixelsTypedouble
from omeroweb.webclient.decorators import login_required
from omeroweb.webgateway.views import _table_query
from omeroweb.webgateway.marshal import channelMarshal


# @login_required()
def index(request, conn=None, **kwargs):
    """
    OMERO Vitessce Home page 
    """
    return HttpResponse(
        "To open an OMERO.table or CSV using it's File ID, go to /vitessce/table/ID"
    )


def get_table_data(conn, file_id, sample_size=None):
    orig_file = conn.getObject("originalfile", file_id)
    file_name = orig_file.getName()
    if file_name.endswith("csv"):
        columns = []
        rows = []
        csvfile = orig_file.asFileObj()
        df = pd.read_csv(csvfile)

        def col_type_str(coltype):
            t = str(coltype)
            return "number" if t.startswith('int') or t.startswith('float') else "string"

        for name, col_type in zip(df.columns, df.dtypes):
            columns.append({
                'name': name, 'type': col_type_str(col_type)
            })
        sample = df
        if sample_size is not None:
            sample = df.head(sample_size)
        for index, row in sample.iterrows():
            rows.append(row)
        csvfile.close()
    else:
        r = conn.getSharedResources()
        table = r.openTable(OriginalFileI(file_id), conn.SERVICE_OPTS)
        if sample_size is None:
            sample_size = table.getNumberOfRows()
        try:
            columns = [
                {'name': col.name,
                'type': "number" if col.__class__.__name__ == "DoubleColumn" else "string"}
                for col in table.getHeaders()
            ]
            res = table.slice(range(len(columns)), range(sample_size))
            rows = [
                [col.values[row] for col in res.columns]
                for row in range(0, len(res.rowNumbers))
            ]

        finally:
            table.close()

    return {'rows': rows, 'columns': columns}


@login_required()
def omero_table(request, file_id, conn=None, **kwargs):
    """Shows the table columns, allowing user to pick"""

    context = get_table_data(conn, file_id, sample_size=5)
    index_url = request.build_absolute_uri(reverse('vitessce_index'))

    # look for Image ID in table data
    col_names = [col["name"] for col in context["columns"]]
    image_col = None
    if "Image" in col_names:
        image_col = col_names.index("Image")
    elif "image_id" in col_names:
        image_col = col_names.index("image_id")
    if image_col is not None:
        context["image_id"] = context["rows"][0][image_col]

    context['table_id'] = file_id
    context['index_url'] = index_url
    template = "omero_vitessce/omero_table.html"
    return render(request, template, context)


class VitessceShape():

    def __init__(self, shape):
        self.shape = self.toShapely(shape)

    def toShapely(self, omero_shape):
        encoder = get_encoder(omero_shape.__class__)
        shape_json = encoder.encode(omero_shape)

        if "Points" in shape_json:
            xy = shape_json["Points"].split(" ")
            coords = []
            for coord in xy:
                c = coord.split(",")
                coords.append((float(c[0]), float(c[1])))
            return Polygon(coords)

    def xy(self):
        return list(self.shape.centroid.coords)[0]

    def poly(self):
        # Use 2 to get e.g. 8 points from 56.
        return list(self.shape.simplify(2).exterior.coords)


@login_required()
def vitessce_config(request, fileid, col1, col2, conn=None, **kwargs):
    """
    Returns a Vitessce config that will load scatterplot data from
    specified fileid (csv or table) and columns
    """

    index_url = request.build_absolute_uri(reverse('vitessce_index'))
    cells_url = f'{index_url}table_vitessce_cells/{fileid}/{col1}/{col2}/'

    image_id = request.GET.get('image')
    if image_id:
        try:
            image_id = int(image_id)
            zarr_url = request.build_absolute_uri(reverse('vitessce_index')) + f'zarr/{image_id}.zarr'
        except:
            # user provided a URL to a zarr image
            zarr_url = image_id

    # Testing: s3 and minio images show channels in the layerController component
    # but other URLs don't
    # zarr_url = "https://s3.embassy.ebi.ac.uk/idr/zarr/v0.1/179706.zarr"
    # zarr_url = "https://minio-dev.openmicroscopy.org/idr/idr0077-valuchova-flowerlightsheet/zscale_01/9836831.zarr"

    desc = "Loading data from OMERO"
    config = {
        "name": "OMERO-Vitessce",
        "description": desc,
        "version": "1.0.0",
        "initStrategy": "auto",
        "datasets": [
            {
                "uid": "omero",
                "name": "OMERO",
                "files": [
                    {
                        "type": "cells",
                        "fileType": "cells.json",
                        "url": cells_url
                    },
                    {
                        "type": "raster",
                        "fileType": "raster.ome-zarr",
                        "url": zarr_url
                    }
                ]
            }
        ],
        "coordinationSpace": {
            "embeddingType": {
                "PCA": "PCA"
            },
            "spatialZoom": {
                "A": -1
            },
            "spatialTargetX": {
                "A": 500
            },
            "spatialTargetY": {
                "A": 300
            }
        },
        "layout": [
            {
                "component": "description",
                "props": {
                    "description": desc
                },
                "x": 0,
                "y": 0,
                "w": 2,
                "h": 1
            },
            {
                "component": "layerController",
                "x": 0,
                "y": 1,
                "w": 2,
                "h": 4
            },
            {
                "component": "status",
                "x": 0,
                "y": 5,
                "w": 2,
                "h": 1
            },
            {
                "component": "spatial",
                "coordinationScopes": {
                    "spatialZoom": "A",
                    "spatialTargetX": "A",
                    "spatialTargetY": "A"
                },
                "x": 2,
                "y": 0,
                "w": 5,
                "h": 6
            },
            {
                "component": "scatterplot",
                "coordinationScopes": {
                    "embeddingType": "PCA"
                },
                "x": 7,
                "y": 0,
                "w": 5,
                "h": 6
            }
        ]
    }
    return JsonResponse(config)


@login_required()
def vitessce_cells(request, fileid, col1, col2, conn=None, **kwargs):
    """
    Return JSON for vitessce viewer cells.json based on a csv or OMERO.table
    http://beta.vitessce.io/docs/data-file-types/index.html#cellsjson

    If there is an ROI or Shape column, load Shape coords and 
    add 'xy' centre point and 'poly' outline coords.

    "cell_1": {
        "mappings": {
            "PCA": [-11.0776, 6.0311]
        }
        "xy": [6824,26313],
        "poly": [
            [6668, 26182],
            [6668, 26296],
            [6873, 26501],
            [6932, 26501],
            [6955, 26478],
            [6955, 26260],
            [6838, 26143],
            [6707, 26143
        ]
    }
    """

    # Get whole table as JSON
    table_data = get_table_data(conn, fileid)

    col_names = [c["name"] for c in table_data["columns"]]
    rows = table_data["rows"]

    col1_index = col_names.index(col1)
    col2_index = col_names.index(col2)
    if col1_index < 0:
        raise Exception("Column not found: %s" % col1)
    if col2_index < 0:
        raise Exception("Column not found: %s" % col2)

    # id_column = None
    # for dtype in ["Roi", "roi_id", "Image", "Well"]:
    #     if dtype in col_names:
    #         id_column = col_names.index(dtype)
    #         break

    id_column = None
    if "shape_id" in col_names:
        id_column = col_names.index("shape_id")
    elif "Shape" in col_names:
        id_column = col_names.index("Shape")

    rv = {}

    shape_ids = []

    for count, row in enumerate(rows):
        if id_column is not None:
            row_key = str(row[id_column])
            shape_ids.append(row[id_column])
        else:
            row_key = "cell_%s" % (count + 1)
        val1 = row[col1_index]
        val2 = row[col2_index]
        rv[row_key] = {"mappings": {"PCA": [val1, val2]}}

    # Load Shapes:
    if len(shape_ids) > 0:
        shapes = conn.getObjects("shape", shape_ids)
        for shape in shapes:
            row_key = str(shape.id)
            vs = VitessceShape(shape._obj)
            rv[row_key]['xy'] = vs.xy()
            rv[row_key]['poly'] = vs.poly()

    return JsonResponse(rv)


@login_required()
def zarr_zattrs(request, iid, conn=None, **kwargs):

    image = conn.getObject("Image", iid)

    rv = {
        "multiscales": [
            {
                "datasets": [
                    {
                        "path": "0"
                    }
                ],
                "version": "0.1"
            }
        ],
        "omero": {
            "channels": [channelMarshal(x) for x in image.getChannels()],
            "id": image.id,
            "rdefs": {
                "defaultT": image._re.getDefaultT(),
                "defaultZ": image._re.getDefaultZ(),
                "model": (image.isGreyscaleRenderingModel() and "greyscale" or "color"),
            }
        }
    }
    return JsonResponse(rv)


def zarr_zgroup(request, **kwargs):
    return JsonResponse({"zarr_format": 2})


@login_required()
def zarr_zarray(request, iid, level, conn=None, **kwargs):

    image = conn.getObject("Image", iid)
    shape = [getattr(image, 'getSize' + dim)() for dim in ('TCZYX')]
    chunks = (1, 1, 1, shape[3], shape[4])

    ptype = image.getPrimaryPixels().getPixelsType().getValue()
    pixelTypes = {
        PixelsTypeint8: np.int8,
        PixelsTypeuint8: np.uint8,
        PixelsTypeint16: np.int16,
        PixelsTypeuint16: np.uint16,
        PixelsTypeint32: np.int32,
        PixelsTypeuint32: np.uint32,
        PixelsTypefloat: np.float32,
        PixelsTypedouble: np.float64
    }
    np_type = pixelTypes[ptype]

    rsp = {"data": "fail"}
    with tempfile.TemporaryDirectory() as tmpdirname:
        # writes zarray
        zarr.open_array(tmpdirname, mode='w', shape=tuple(shape), chunks=chunks, dtype=np_type)

        # reads zarray
        zattrs_path = os.path.join(tmpdirname, '.zarray')
        with open(zattrs_path, 'r') as reader:
            json_text = reader.read()
            rsp = json.loads(json_text)

    return JsonResponse(rsp)


@login_required()
def zarr_chunk(request, iid, level, t, c, z, y, x, conn=None, **kwargs):

    x, y, z, c, t = [int(dim) for dim in (x, y, z, c, t)]

    # NB: Assume that x and y are 0 and we are loading whole z, c, t plane
    image = conn.getObject("Image", iid)
    shape = [getattr(image, 'getSize' + dim)() for dim in ('TCZYX')]
    chunks = (1, 1, 1, shape[3], shape[4])

    plane = image.getPrimaryPixels().getPlane(z, c, t)
    data = ""
    chunk_name = ".".join([str(dim) for dim in [t, c, z, y, x]])
    with tempfile.TemporaryDirectory() as tmpdirname:
        # write chunk
        zarr_array = zarr.open_array(tmpdirname, mode='w', shape=tuple(shape), chunks=chunks, dtype=plane.dtype)
        zarr_array[t, c, z, :, :] = plane

        # reads zarray
        chunk_path = os.path.join(tmpdirname, chunk_name)
        with open(chunk_path, 'rb') as reader:
            data = reader.read()

    rsp = HttpResponse(data)
    rsp["Content-Length"] = len(data)
    rsp["Content-Disposition"] = "attachment; filename=%s" % chunk_name
    return rsp
