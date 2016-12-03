from __future__ import absolute_import
from __future__ import print_function

import os.path

from unittest import TestCase

import matplotlib

matplotlib.use('TkAgg')

#-------------------------
def test_icm_dpqf():
    """
    Let the user test the software!!!

    Please use the code as tutorial
    """
    from .get_data_dir import get_data_dir
    from ..icm_io import ICMio
    from ..s5p_plot import S5Pplot

    # obtain path to directory pys5p-data
    data_dir = get_data_dir()
    if data_dir is None:
        return
    fl_name = 'S5P_TEST_ICM_CA_SIR_20120918T131651_20120918T145629_01890_01_001100_20151002T140000.h5'
    icm_product = os.path.join(data_dir, fl_name)

    # open ICM product
    icm = ICMio( icm_product )
    if len(icm.select('DPQF_MAP')) > 0:
        dpqm = icm.get_msm_data( 'dpqf_map', band='78' )

        dpqm_dark = icm.get_msm_data( 'dpqm_dark_flux', band='78' )

        dpqm_noise = icm.get_msm_data( 'dpqm_noise', band='78' )

    # generate figure
    plot = S5Pplot('test_icm_dpq.pdf')
    plot.draw_quality(dpqm,
                      title=fl_name,
                      sub_title='dpqf_map')
    plot.draw_quality(dpqm_dark,
                      title=fl_name,
                      sub_title='dpqm_dark_flux')
    plot.draw_quality(dpqm_noise,
                      title=fl_name,
                      sub_title='dpqm_noise')
    del plot
    del icm
    

class TestCmd(TestCase):
    def test_basic(self):
        test_icm_dpqf()
