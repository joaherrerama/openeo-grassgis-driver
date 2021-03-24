# -*- coding: utf-8 -*-
from flask_restful import Resource
from flask import make_response, jsonify, request
from openeo_grass_gis_driver.actinia_processing.actinia_interface import ActiniaInterface
from openeo_grass_gis_driver.models.collection_schemas import CollectionInformation, CollectionExtent, EoLinks
from openeo_grass_gis_driver.models.collection_schemas import CollectionProperties, EOBands
from osgeo import osr, ogr

__license__ = "Apache License, Version 2.0"
__author__ = "Sören Gebbert"
__copyright__ = "Copyright 2018, Sören Gebbert, mundialis"
__maintainer__ = "Soeren Gebbert"
__email__ = "soerengebbert@googlemail.com"

strds_example = {
    "aggregation_type": "None",
    "bottom": "0.0",
    "creation_time": "2016-08-11 16:44:29.756411",
    "creator": "soeren",
    "east": "75.5",
    "end_time": "2013-07-01 00:00:00",
    "ewres_max": "0.25",
    "ewres_min": "0.25",
    "granularity": "1 month",
    "id": "precipitation_1950_2013_monthly_mm@PERMANENT",
    "map_time": "interval",
    "mapset": "PERMANENT",
    "max_max": "1076.9",
    "max_min": "168.9",
    "min_max": "3.2",
    "min_min": "0.0",
    "modification_time": "2016-08-11 16:45:14.032432",
    "name": "precipitation_1950_2013_monthly_mm",
    "north": "75.5",
    "nsres_max": "0.25",
    "nsres_min": "0.25",
    "number_of_maps": "762",
    "raster_register": "raster_map_register_934719ed2b4841818386a6f9c5f11b09",
    "semantic_type": "mean",
    "south": "25.25",
    "start_time": "1950-01-01 00:00:00",
    "temporal_type": "absolute",
    "top": "0.0",
    "west": "-40.5"
}

raster_example = {
    "cells": "2025000",
    "cols": "1500",
    "comments": "\"r.proj input=\"ned03arcsec\" location=\"northcarolina_latlong\" mapset=\"\\helena\" output=\"elev_ned10m\" method=\"cubic\" resolution=10\"",
    "creator": "\"helena\"",
    "database": "/tmp/gisdbase_75bc0828",
    "datatype": "FCELL",
    "date": "\"Tue Nov  7 01:09:51 2006\"",
    "description": "\"generated by r.proj\"",
    "east": "645000",
    "ewres": "10",
    "location": "nc_spm_08",
    "map": "elevation",
    "mapset": "PERMANENT",
    "max": "156.3299",
    "min": "55.57879",
    "ncats": "255",
    "north": "228500",
    "nsres": "10",
    "rows": "1350",
    "source1": "\"\"",
    "source2": "\"\"",
    "south": "215000",
    "timestamp": "\"none\"",
    "title": "\"South-West Wake county: Elevation NED 10m\"",
    "units": "\"none\"",
    "vdatum": "\"none\"",
    "west": "630000"
}


def coordinate_transform_extent_to_EPSG_4326(crs: str, extent: CollectionExtent):
    """Tranfor the extent coordinates to lat/lon

    :param crs:
    :param extent:
    :return:
    """

    source = osr.SpatialReference()
    source.ImportFromWkt(crs)

    target = osr.SpatialReference()
    target.ImportFromEPSG(4326)

    transform = osr.CoordinateTransformation(source, target)

    lower_left = ogr.CreateGeometryFromWkt(f"POINT ({extent.spatial['bbox'][0][0]} {extent.spatial['bbox'][0][1]})")
    lower_left.Transform(transform)
    upper_right = ogr.CreateGeometryFromWkt(f"POINT ({extent.spatial['bbox'][0][2]} {extent.spatial['bbox'][0][3]})")
    upper_right.Transform(transform)

    a0 = lower_left.GetPoint()[0]
    a1 = lower_left.GetPoint()[1]
    a2 = upper_right.GetPoint()[0]
    a3 = upper_right.GetPoint()[1]

    extent.spatial['bbox'][0] = (a0, a1, a2, a3)
    return extent


class CollectionInformationResource(Resource):

    def __init__(self):
        self.iface = ActiniaInterface()

    def get(self, name):

        # List strds maps from the GRASS location
        location, mapset, datatype, layer = self.iface.layer_def_to_components(name)

        status_code, layer_data = self.iface.layer_info(layer_name=name)
        if status_code != 200:
            return make_response(jsonify({"id": "12345678",
                                          "code": "CollectionNotFound",
                                          "message": "Collection '%s' does not exist." % (name),
                                          "links": {}}),
                                          404)

        # Get the projection from the GRASS mapset
        status_code, mapset_info = self.iface.mapset_info(location=location, mapset=mapset)
        if status_code != 200:
            return make_response(jsonify({"id": "12345678",
                                          "code": "Internal",
                                          "message": "Server error: %s" % (mapset_info),
                                          "links": {}}),
                                          500)

        extent = CollectionExtent(spatial=(float(layer_data["west"]), float(layer_data["south"]),
                                           float(layer_data["east"]), float(layer_data["north"])),
                                  temporal=("1900-01-01T00:00:00", "2100-01-01T00:00:00"))

        title = "Raster dataset"
        bands = []
        dimensions = {"x": {
            "type": "spatial",
            "axis": "x"
        },
            "y": {
            "type": "spatial",
            "axis": "x"
        },
        }
        if datatype.lower() == "strds":
            title = "Space time raster dataset"

            start_time = layer_data["start_time"]
            end_time = layer_data["end_time"]

            if start_time:
                start_time = start_time.replace(" ", "T").replace("'", "").replace('"', '')

            if end_time:
                end_time = end_time.replace(" ", "T").replace("'", "").replace('"', '')

            dimensions['t'] = {"type": "temporal",
                               "extent": [start_time, end_time]
                               }

            extent = CollectionExtent(spatial=(float(layer_data["west"]), float(layer_data["south"]),
                                               float(layer_data["east"]), float(layer_data["north"])),
                                      temporal=(start_time, end_time))

            # TODO: band_names must be in layer_data
            if "number_of_bands" in layer_data:
                if layer_data["number_of_bands"] == "13":
                    bands.append(EOBands(name="S2_1", common_name="coastal"))
                    bands.append(EOBands(name="S2_2", common_name="blue"))
                    bands.append(EOBands(name="S2_3", common_name="green"))
                    bands.append(EOBands(name="S2_4", common_name="red"))
                    bands.append(EOBands(name="S2_5", common_name="rededge"))
                    bands.append(EOBands(name="S2_6", common_name="rededge"))
                    bands.append(EOBands(name="S2_7", common_name="rededge"))
                    bands.append(EOBands(name="S2_8", common_name="nir"))
                    bands.append(EOBands(name="S2_8A", common_name="nir08"))
                    bands.append(EOBands(name="S2_9", common_name="nir09"))
                    bands.append(EOBands(name="S2_10", common_name="cirrus"))
                    bands.append(EOBands(name="S2_11", common_name="swir16"))
                    bands.append(EOBands(name="S2_12", common_name="swir22"))

                    dimensions['bands'] = {"type": "bands",
                                           "values": ["coastal",
                                                      "blue",
                                                      "green",
                                                      "rededge",
                                                      "rededge",
                                                      "rededge",
                                                      "nir",
                                                      "nir08",
                                                      "nir09",
                                                      "cirrus",
                                                      "swir16",
                                                      "swir22"
                                                      ]
                                           }

        if datatype.lower() == "vector":
            title = "Vector dataset"

        description = "GRASS GIS location/mapset path: /%s/%s" % (location, mapset)
        crs = mapset_info["projection"]

        coordinate_transform_extent_to_EPSG_4326(crs=crs, extent=extent)

        properties = (CollectionProperties(eo_platform="Sentinel-2",
                                           eo_instrument="Sentinel-2",
                                           eo_bands=bands))

        ci = CollectionInformation(id=name, title=title,
                                   description=description,
                                   extent=extent,
                                   properties=properties,
                                   dimensions=dimensions)

        return ci.as_response(http_status=200)
