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
from shapely.geometry import Polygon
from omero_marshal import get_encoder

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.core.urlresolvers import reverse

from omero.model import OriginalFileI
from omeroweb.webclient.decorators import login_required
from omeroweb.webgateway.views import _table_query


# @login_required()
def index(request, conn=None, **kwargs):
    """
    OMERO Vitessce Home page 
    """
    return HttpResponse(
        "To open an OMERO.table using it's File ID, go to /vitessce/table/ID"
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
    context['table_id'] = file_id
    context['index_url'] = index_url
    template = "omero_vitessce/omero_table.html"
    return render(request, template, context)


# >>> polygon = Polygon([(0, 0), (1, 1), (1, 0)])
# >>> polygon.area
# 0.5
# >>> polygon.length
# 3.4142135623730949
# Its x-y bounding box is a (minx, miny, maxx, maxy) tuple.

# >>> polygon.bounds
# (0.0, 0.0, 1.0, 1.0)


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