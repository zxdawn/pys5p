"""
This file is part of pyS5p

https://github.com/rmvanhees/pys5p.git

The class LV2io provides read access to S5p Tropomi S5P_OFFL_L2 products

Copyright (c) 2018 SRON - Netherlands Institute for Space Research
   All Rights Reserved

License:  BSD-3-Clause
"""
from pathlib import Path

import h5py
import numpy as np

# - global parameters ------------------------------

# - local functions --------------------------------


# - class definition -------------------------------
class LV2io():
    """
    This class should offer all the necessary functionality to read Tropomi
    S5P_OFFL_L2 products
    """
    def __init__(self, lv2_product):
        """
        Initialize access to an S5P_L2 product

        Parameters
        ----------
        lv2_product :  string
           full path to S5P Tropomi level 2 product
        """
        # initialize class-attributes
        self.filename = lv2_product
        self.fid = None

        if not Path(lv2_product).is_file():
            raise FileNotFoundError('{} does not exist'.format(lv2_product))

        # open LV2 product as HDF5 file
        self.fid = h5py.File(lv2_product, "r")

    def __repr__(self):
        class_name = type(self).__name__
        return '{}({!r})'.format(class_name, self.filename)

    def __iter__(self):
        for attr in sorted(self.__dict__):
            if not attr.startswith("__"):
                yield attr

    def __del__(self):
        """
        called when the object is destroyed
        """
        self.close()

    def __enter__(self):
        """
        method called to initiate the context manager
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        method called when exiting the context manager
        """
        self.close()
        return False  # any exception is raised by the with statement.

    def close(self):
        """
        Close the product.
        """
        if self.fid is not None:
            self.fid.close()

    # -------------------------
    def get_orbit(self):
        """
        Returns reference orbit number
        """
        if 'orbit' in self.fid.attrs:
            return int(self.fid.attrs['orbit'])

        return None

    def get_algorithm_version(self):
        """
        Returns version of the level 2 algorithm
        """
        if 'algorithm_version' not in self.fid.attrs:
            return None

        res = self.fid.attrs['algorithm_version']
        if isinstance(res, bytes):
            return res.decode('ascii')

        return res

    def get_product_version(self):
        """
        Returns version of the level 2 product
        """
        if 'product_version' not in self.fid.attrs:
            return None

        res = self.fid.attrs['product_version']
        if isinstance(res, bytes):
            return res.decode('ascii')

        return res

    def get_coverage_time(self):
        """
        Returns start and end of the measurement coverage time
        """
        if 'time_coverage_start' not in self.fid.attrs \
           or 'time_coverage_end' not in self.fid.attrs:
            return None

        res1 = self.fid.attrs['time_coverage_start']
        if isinstance(res1, bytes):
            res1 = res1.decode('ascii')

        res2 = self.fid.attrs['time_coverage_end']
        if isinstance(res2, bytes):
            res2 = res2.decode('ascii')

        return (res1, res2)

    def get_creation_time(self):
        """
        Returns creation date/time of the level 2 product
        """
        if 'date_created' not in self.fid.attrs:
            return None

        res = self.fid.attrs['date_created']
        if isinstance(res, bytes):
            return res.decode('ascii')

        return res

    def get_attr(self, attr_name):
        """
        Obtain value of an HDF5 file attribute

        Parameters
        ----------
        attr_name : string
           name of the attribute
        """
        if attr_name not in self.fid.attrs:
            return None

        res = self.fid.attrs[attr_name]
        if isinstance(res, bytes):
            return res.decode('ascii')

        return res

    # ---------- Functions using data in the PRODUCT group ----------
    def get_ref_time(self):
        """
        Returns reference start time of measurements
        """
        from datetime import datetime, timedelta

        ref_time = datetime(2010, 1, 1, 0, 0, 0)
        ref_time += timedelta(seconds=int(self.fid['/PRODUCT/time'][0]))
        return ref_time

    def get_delta_time(self):
        """
        Returns offset from the reference start time of measurement
        """
        return self.fid['/PRODUCT/delta_time'][0, :].astype(int)

    def get_geo_data(self,
                     geo_dset='satellite_latitude,satellite_longitude'):
        """
        Returns data of selected datasets from the GEOLOCATIONS group

        Parameters
        ----------
        geo_dset  :  string
            Name(s) of datasets in the GEODATA group, comma separated
            Default is 'satellite_latitude,satellite_longitude'

        Returns
        -------
        out   :   array-like
           Compound array with data of selected datasets from the GEODATA group
        """
        grp = self.fid['/PRODUCT/SUPPORT_DATA/GEOLOCATIONS']
        for key in geo_dset.split(','):
            if res is None:
                res = np.squeeze(grp[key])
            else:
                res = np.append(res, np.squeeze(grp[key]))

        return res

    def get_geo_bounds(self):
        """
        Returns bounds of latitude/longitude as a mesh for plotting

        Returns
        -------
        out   :   dictionary
           with numpy arrays for latitude and longitude
        """
        gid = self.fid['/PRODUCT/SUPPORT_DATA/GEOLOCATIONS']
        _sz = gid['latitude_bounds'].shape

        res = {}
        res['latitude'] = np.empty((_sz[1]+1, _sz[2]+1), dtype=float)
        res['latitude'][:-1, :-1] = gid['latitude_bounds'][0, :, :, 0]
        res['latitude'][-1, :-1] = gid['latitude_bounds'][0, -1, :, 1]
        res['latitude'][:-1, -1] = gid['latitude_bounds'][0, :, -1, 1]
        res['latitude'][-1, -1] = gid['latitude_bounds'][0, -1, -1, 2]

        res['longitude'] = np.empty((_sz[1]+1, _sz[2]+1), dtype=float)
        res['longitude'][:-1, :-1] = gid['longitude_bounds'][0, :, :, 0]
        res['longitude'][-1, :-1] = gid['longitude_bounds'][0, -1, :, 1]
        res['longitude'][:-1, -1] = gid['longitude_bounds'][0, :, -1, 1]
        res['longitude'][-1, -1] = gid['longitude_bounds'][0, -1, -1, 2]
        return res

    def get_msm_data(self, name, fill_as_nan=True):
        """
        Read level 2 data

        Parameters
        ----------
        name   :  string
            name of dataset with level 2 data
        fill_as_nan :  boolean
            Replace (float) FillValues with Nan's, when True

        Returns
        -------
        out  :  array
        """
        fillvalue = float.fromhex('0x1.ep+122')

        dset = self.fid['/PRODUCT/{}'.format(name)]
        if dset.dtype == np.float32:
            res = np.squeeze(dset).astype(np.float64)
        else:
            res = np.squeeze(dset)
        if fill_as_nan and dset.attrs['_FillValue'] == fillvalue:
            res[(res == fillvalue)] = np.nan
        return res