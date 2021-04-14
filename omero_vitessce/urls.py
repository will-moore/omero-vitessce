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

from django.conf.urls import url

from . import views

urlpatterns = [

    # index 'home page' of the app
    url(r'^$', views.index, name="vitessce_index"),

    url(r'^table/(?P<file_id>[0-9]+)/$', views.omero_table, name="vitessce_omero_table"),

    url(r"^vitessce_config/(?P<fileid>[0-9]+)/(?P<col1>[^/]+)/(?P<col2>[^/]+)/$",
        views.vitessce_config, name="vitessce_config"),

    url(r"^table_vitessce_cells/(?P<fileid>[0-9]+)/(?P<col1>[^/]+)/(?P<col2>[^/]+)/$",
        views.vitessce_cells, name="vitessce_cells"),

    # zarr
    # url(r"^zarr/(?P<url>.+)", views.vitessce_zarr, name="vitessce_zarr")

    url(r'^zarr/(?P<iid>[0-9]+).zarr/.zattrs$',
        views.zarr_zattrs, name='vitessce_zarr_zattrs'),

    url(r'^zarr/(?P<iid>[0-9]+).zarr/.zgroup$',
        views.zarr_zgroup, name='vitessce_zarr_zgroup'),

    url(r'^zarr/(?P<iid>[0-9]+).zarr/(?P<level>[0-9]+)/.zarray$',
        views.zarr_zarray, name='vitessce_zarr_zarray'),

    url(r'^zarr/(?P<iid>[0-9]+).zarr/(?P<level>[0-9]+)/(?P<t>[0-9]+).(?P<c>[0-9]+).(?P<z>[0-9]+).(?P<y>[0-9]+).(?P<x>[0-9]+)$',
        views.zarr_chunk, name='vitessce_zarr'),
]