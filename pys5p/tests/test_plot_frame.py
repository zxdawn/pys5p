"""
This file is part of pyS5p

https://github.com/rmvanhees/pys5p.git

Purpose
-------
Perform unittest on S5Pplot.draw_signal

Note
----
Please use the code as tutorial

Copyright (c) 2017 SRON - Netherlands Institute for Space Research
   All Rights Reserved

License:  Standard 3-clause BSD

"""
from __future__ import absolute_import
from __future__ import print_function

import os.path

from glob import glob
#from unittest import TestCase

#-------------------------
def test_frame():
    """
    Check class OCMio and S5Pplot.draw_signal

    """
    from ..get_data_dir import get_data_dir
    from ..ocm_io import OCMio
    from ..s5p_plot import S5Pplot

    # obtain path to directory pys5p-data
    try:
        data_dir = get_data_dir()
    except FileNotFoundError:
        return
    if not os.path.isdir(os.path.join(data_dir, 'OCM')):
        return
    msmlist = glob(os.path.join(data_dir, 'OCM', '*'))
    sdirlist = glob(os.path.join(msmlist[0], '*'))

    # read background measurements
    icid = 31523

    # Read BAND7 product
    product_b7 = 'trl1brb7g.lx.nc'
    ocm_product = os.path.join(sdirlist[0], product_b7)

    # open OCAL Lx poduct
    ocm7 = OCMio(ocm_product)

    # select data of measurement(s) with given ICID
    if ocm7.select(icid) > 0:
        dict_b7 = ocm7.get_msm_data('signal')
        dict_b7_std = ocm7.get_msm_data('signal_error_vals')

    # Read BAND8 product
    product_b8 = 'trl1brb8g.lx.nc'
    ocm_product = os.path.join(sdirlist[0], product_b8)

    # open OCAL Lx poduct
    ocm8 = OCMio(ocm_product)

    # select data of measurement(s) with given ICID
    if ocm8.select(icid) > 0:
        dict_b8 = ocm8.get_msm_data('signal')
        dict_b8_std = ocm8.get_msm_data('signal_error_vals')

    # Combine band 7 & 8 data
    for key in dict_b7:
        print(key, dict_b7[key].shape)
    data = ocm7.band2channel(dict_b7, dict_b8,
                             mode=['combine', 'median'],
                             skip_first=True, skip_last=True)
    error = ocm7.band2channel(dict_b7_std, dict_b8_std,
                              mode=['combine', 'median'],
                              skip_first=True, skip_last=True)

    # Generate figure
    plot = S5Pplot('test_plot_frame.pdf')
    plot.draw_signal(data,
                     title=ocm7.get_attr('title'),
                     sub_title='signal ICID={}'.format(icid),
                     fig_info=None)
    plot.draw_signal(error,
                     title=ocm7.get_attr('title'),
                     sub_title='signal_error_vals ICID={}'.format(icid),
                     fig_info=None)
    plot.draw_hist(data, error,
                   error_label='signal_error_vals',
                   title=ocm7.get_attr('title'),
                   sub_title='signal ICID={}'.format(icid),
                   fig_info=None)
    del plot
    del ocm7
    del ocm8

if __name__ == '__main__':
    test_frame()
