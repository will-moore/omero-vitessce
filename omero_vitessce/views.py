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


@login_required()
def omero_table(request, file_id, conn=None, **kwargs):
    """Shows the table columns, allowing user to pick"""

    r = conn.getSharedResources()
    table = r.openTable(OriginalFileI(file_id), conn.SERVICE_OPTS)
    table_data = []
    batch = 5
    try:
        # table_data = [{'name': col.name, 'rows': []} for col in table.getHeaders()]
        res = table.slice(range(len(table_data)), range(batch))

        # for row in range(0, batch):
        #     for idx, col in enumerate(rows.columns):
        #         table_data[idx]['rows'].append(col.values[row])

        columns = [
            {'name': col.name,
             'type': col.__class__.__name__}
             for col in table.getHeaders()
        ]
        rows = [
            [col.values[row] for col in res.columns]
            for row in range(0, len(res.rowNumbers))
        ]

    finally:
        table.close()

    # return JsonResponse({'columns': columns, 'rows': rows})
    index_url = request.build_absolute_uri(reverse('vitessce_index'))

    template = "omero_vitessce/omero_table.html"
    return render(request, template, {
        'table_id': file_id,
        'columns': columns,
        'rows': rows,
        'index_url': index_url})


@login_required()
def vitessce_cells(request, fileid, col1, col2, conn=None, **kwargs):
    """
    Return JSON for vitessce viewer cells.json
    http://beta.vitessce.io/docs/data-file-types/index.html#cellsjson
    "cell_1": {
        "mappings": {
            "t-SNE": [-11.0776, 6.0311]
        }
    }
    """

    # Get whole table as JSON (TODO: just query the columns we need)
    table_dict = _table_query(request, fileid, conn, query="*")

    col_names = table_dict["data"]["columns"]
    rows = table_dict["data"]["rows"]

    col1_index = col_names.index(col1)
    col2_index = col_names.index(col2)
    if col1_index < 0:
        raise Exception("Column not found: %s" % col1)
    if col2_index < 0:
        raise Exception("Column not found: %s" % col2)

    id_column = None
    for dtype in ["Roi", "Image", "Well"]:
        if dtype in col_names:
            id_column = col_names.index(dtype)
            break

    rv = {}

    for count, row in enumerate(rows):
        row_id = row[id_column]
        val1 = row[col1_index]
        val2 = row[col2_index]
        rv["cell_%s" % (count + 1)] = {"mappings": {"UMAP": [val1, val2]}}

    return JsonResponse(rv)