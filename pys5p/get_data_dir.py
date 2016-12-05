from __future__ import absolute_import

import os.path

from os import environ

def get_data_dir():
    """
    Obtain directory with test datasets

    Limited to UNIX/Linux/MacOS operating systems

    This module checks if the following directories are available:
     - /data/$USER/pys5p-data
     - /Users/$USER/pys5p-data
     - environment variable PYS5P_DATA_DIR

    It expects the data to be organized in the sub-directories:
     - CKD which should contain the SWIR dpqf CKD
     - OCM which should contain at least one directory of an on-ground
       calibration measurement with one or more OCAL LX products.
     - L1B which should contain at least one offline calibration, irradiance
       and radiance product.
     - ICM which contain at least one inflight calibration product.
    """
    try:
        user = environ['USER']
    except KeyError:
        print('*** Fatal: environment variable USER not set')
        return None

    guesses_data_dir = ['/data/{}/pys5p-data'.format(user),
                        '/Users/{}/pys5p-data'.format(user)]

    try:
        _ = environ['PYS5P_DATA_DIR']
    except KeyError:
        pass
    else:
        guesses_data_dir.append(environ['PYS5P_DATA_DIR'])

    for key in guesses_data_dir:
        if os.path.isdir(key):
            print(key)
            return key

    raise FileNotFoundError