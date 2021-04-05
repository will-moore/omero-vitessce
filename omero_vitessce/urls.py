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

    url(r"^table_vitessce_cells/(?P<fileid>[0-9]+)/(?P<col1>[^/]+)/(?P<col2>[^/]+)/$",
        views.vitessce_cells, name="vitessce_cells")
]