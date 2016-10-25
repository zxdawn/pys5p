'''
This file is part of pys5p

https://github.com/rmvanhees/pys5p.git

The class ICMplot contains generic plot functions to display S5p Tropomi data

-- generate figures --
 Public functions a page in the output PDF
 * draw_signal
 * draw_errors
 * draw_hist
 * draw_quality

Copyright (c) 2016 SRON - Netherlands Institute for Space Research
   All Rights Reserved

License:  Standard 3-clause BSD

'''
import os.path
from collections import OrderedDict

import numpy as np

import matplotlib as mpl

mpl.use('TkAgg')

#
# Suggestion for the name of the report/pdf-file
#    <identifier>_<yyyymmdd>_<orbit>.pdf
# where
#  identifier : name of L1B/ICM/OCM product or monitoring database
#  yyyymmdd   : coverage start-date or start-date of monitoring entry
#  orbit      : reference orbit
#
# Suggestion for info-structure to be displayed in figure
# * Versions used to generate the data:
#   algo_version : version of monitoring algorithm (SRON)
#   db_version   : version of the monitoring database (SRON)
#   l1b_version  : L1b processor version
#   icm_version  : ICM processor version
# * Data in detector coordinates or column/row averaged as function of time
#   sign_median  : (biweight) median of signals
#   sign_spread  : (biweight) spread of signals
#   error_median : (biweight) median of errors
#   error_spread : (biweight) spread of errors
# * Detector quality data:
#   dpqf_01      : nummer of good pixels with threshold at 0.1
#   dpqf_08      : nummer of good pixels with threshold at 0.8
#
# To force the sequence of the displayed information it is adviced to use
# collections.OrderedDict:
#
# > from collections import OrderedDict
# > dict_info = OrderedDict({key1 : value1})
# > dict_info.update({key2 : value2})
# etc.
#

# pylint: disable=too-many-arguments, too-many-locals
class S5Pplot(object):
    '''
    Generate figure(s) for the SRON Tropomi SWIR monitor website or MPC reports

    The PDF will have the following name:
        <dbname>_<startDateTime of monitor entry>_<orbit of monitor entry>.pdf
    '''
    def __init__( self, figname, cmap="Rainbow", mode='frame' ):
        from matplotlib.backends.backend_pdf import PdfPages

        self.__pdf  = PdfPages( figname )
        self.__cmap = cmap
        self.__mode = mode

    def __repr__( self ):
        pass

    def __del__( self ):
        self.__pdf.close()

    # --------------------------------------------------
    @staticmethod
    def __fig_info( fig, dict_info ):
        '''
        Add meta-information in the current figure
        '''
        from datetime import datetime

        info_str = 'date : ' + datetime.utcnow().isoformat(' ')[0:19]
        for key in dict_info:
            info_str += '\n{} : {}'.format(key, dict_info[key])

        fig.text(0.015, 0.075, info_str,
                 verticalalignment='bottom', horizontalalignment='left',
                 bbox={'facecolor':'white', 'pad':10},
                 fontsize=8, style='italic')
        fig.text(0.025, 0.875,
                 r'$\copyright$ SRON Netherlands Institute for Space Research')

    # --------------------------------------------------
    def __frame( self, signal_in, signal_col_in, signal_row_in,
                 fig_info=None, title=None, sub_title=None,
                 data_label=None, data_unit=None ):
        '''
        Method which actually draws the signal figures
        '''
        from matplotlib import pyplot as plt
        from matplotlib import gridspec

        from pys5p import sron_colorschemes

        sron_colorschemes.register_cmap_rainbow()
        line_colors = sron_colorschemes.get_line_colors()

        signal = np.copy(signal_in)
        signal_col = np.copy(signal_col_in)
        signal_row = np.copy(signal_row_in)
        (p_10, p_90) = np.percentile( signal[np.isfinite(signal)], (10,90) )
        if data_unit is None:
            label = '{}'.format(data_label)
        elif data_unit.find( 'electron' ) >= 0:
            max_value = max(abs(p_10), abs(p_90))
            if max_value > 1000000000:
                signal /= 1000000000
                signal_col /= 1000000000
                signal_row /= 1000000000
                p_10 /= 1000000000
                p_90 /= 1000000000
                label = '{} [{}]'.format(data_label,
                                         data_unit.replace('electron', 'Ge'))
            elif max_value > 1000000:
                signal /= 1000000
                signal_col /= 1000000
                signal_row /= 1000000
                p_10 /= 1000000
                p_90 /= 1000000
                label = '{} [{}]'.format(data_label,
                                         data_unit.replace('electron', 'Me'))
            elif max_value > 1000:
                signal /= 1000
                signal_col /= 1000
                signal_row /= 1000
                p_10 /= 1000
                p_90 /= 1000
                label = '{} [{}]'.format(data_label,
                                         data_unit.replace('electron', 'ke'))
            else:
                label = '{} [{}]'.format(data_label,
                                         data_unit.replace('electron', 'e'))
        else:
            label = '{} [{}]'.format(data_label, data_unit)

        fig = plt.figure(figsize=(18, 7.875))
        if title is not None:
            fig.suptitle( title, fontsize=24 )
        gspec = gridspec.GridSpec(6,16)

        axx = plt.subplot(gspec[1:4,0:2])
        axx.plot(signal_col, np.arange(signal_col.size),
                 lw=0.5, color=line_colors[0])
        axx.set_xlabel( label )
        axx.set_ylim( [0, signal_col.size-1] )
        axx.locator_params(axis='x', nbins=3)
        axx.set_ylabel( 'row' )

        axx = plt.subplot(gspec[1:4,2:14])
        axx.imshow( signal, cmap=self.__cmap, aspect=1, vmin=p_10, vmax=p_90,
                    interpolation='none', origin='lower' )
        if sub_title is not None:
            axx.set_title( sub_title )

        axx = plt.subplot(gspec[4:6,2:14])
        axx.plot(np.arange(signal_row.size), signal_row,
                 lw=0.5, color=line_colors[0])
        axx.set_ylabel( label )
        axx.set_xlim( [0, signal_row.size-1] )
        axx.set_xlabel( 'column' )

        axx = plt.subplot(gspec[1:6,14])
        norm = mpl.colors.Normalize(vmin=p_10, vmax=p_90)
        cb1 = mpl.colorbar.ColorbarBase( axx, cmap=self.__cmap, norm=norm,
                                         orientation='vertical' )
        if data_unit is not None:
            cb1.set_label( label )

        if fig_info is not None:
            self.__fig_info( fig, fig_info )
        plt.tight_layout()
        self.__pdf.savefig()
        plt.close()

    # --------------------------------------------------
    def __hist( self, signal_in, error_in, fig_info,
                data_label=None, data_unit=None,
                error_label=None, error_unit=None,
                title=None, sub_title=None ):
        '''
        Method which actually draws the histogram figures
        '''
        from matplotlib import pyplot as plt
        from matplotlib import gridspec

        from pys5p import sron_colorschemes
        from pys5p.biweight import biweight

        line_colors = sron_colorschemes.get_line_colors()

        if fig_info is None:
            fig_info = OrderedDict({'num_sigma' : 3})

        signal = np.copy(signal_in[np.isfinite(signal_in)]).reshape(-1)
        if 'sign_median' not in fig_info \
            or 'sign_spread' not in fig_info:
            (median, spread) = biweight(signal, spread=True)
            fig_info.update({'sign_median' : median})
            fig_info.update({'sign_spread' : spread})
        signal -= fig_info['sign_median']

        error  = np.copy(error_in[np.isfinite(error_in)]).reshape(-1)
        if 'error_median' not in fig_info \
            or 'error_spread' not in fig_info:
            (median, spread) = biweight(error, spread=True)
            fig_info.update({'error_median' : median})
            fig_info.update({'error_spread' : spread})
        error -= fig_info['error_median']

        if data_unit is not None:
            d_label = '{} [{}]'.format(data_label,
                                       data_unit.replace('electron', 'e'))
        else:
            d_label = data_label

        if error_unit is not None:
            e_label = '{} [{}]'.format(error_label,
                                       error_unit.replace('electron', 'e'))
        else:
            e_label = error_label

        fig = plt.figure(figsize=(18, 7.875))
        if title is not None:
            fig.suptitle( title, fontsize=24 )
        gspec = gridspec.GridSpec(6,8)

        axx = plt.subplot(gspec[1:3,1:])
        axx.hist( signal,
                  range=[-fig_info['num_sigma'] * fig_info['sign_spread'],
                         fig_info['num_sigma'] * fig_info['sign_spread']],
                  bins=15, color=line_colors[0] )
        axx.set_title( r'Histogram is centered at the median with range of ' \
                       r'$\pm 3 \sigma$' )
        axx.set_xlabel( d_label )
        axx.set_ylabel( 'count' )
        if sub_title is not None:
            axx.set_title( sub_title )

        axx = plt.subplot(gspec[3:5,1:])
        axx.hist( error,
                  range=[-fig_info['num_sigma'] * fig_info['error_spread'],
                         fig_info['num_sigma'] * fig_info['error_spread']],
                  bins=15, color=line_colors[0] )
        axx.set_xlabel( e_label )
        axx.set_ylabel( 'count' )

        self.__fig_info( fig, fig_info )
        plt.tight_layout()
        self.__pdf.savefig()
        plt.close()

    # --------------------------------------------------
    def __quality( self, dpqm, low_thres=0.1, high_thres=0.8,
                   title=None, sub_title=None ):
        '''
        Method which actually draws the quality figures
        '''
        from matplotlib import pyplot as plt
        from matplotlib import gridspec

        thres_min = 10 * low_thres
        thres_max = 10 * high_thres
        dpqf = (dpqm * 10).astype(np.int8)
        unused_cols = np.where(np.sum(dpqm, axis=0) < (256 // 4))
        if unused_cols[0].size > 0:
            dpqf[:,unused_cols[0]] = -1
        unused_rows = np.where(np.sum(dpqm, axis=1) < (1000 // 4))
        if unused_rows[0].size > 0:
            dpqf[:,unused_rows[0]] = -1

        fig = plt.figure(figsize=(18, 7.875))
        if title is not None:
            fig.suptitle( title, fontsize=24 )
        gspec = gridspec.GridSpec(6,16)

        clist = ['#BBBBBB', '#EE6677','#CCBB44','w']
        cmap = mpl.colors.ListedColormap(clist)
        bounds=[-1, 0, thres_min, thres_max, 10]
        norm = mpl.colors.BoundaryNorm(bounds, cmap.N)

        dpqf_col_01 = np.sum( ((dpqf >= 0) & (dpqf < thres_min)), axis=1 )
        dpqf_col_08 = np.sum( ((dpqf >= 0) & (dpqf < thres_max)), axis=1 )

        axx = plt.subplot(gspec[1:4,0:2])
        axx.step(dpqf_col_08, np.arange(dpqf_col_08.size),
                 lw=0.5, color=clist[2] )
        axx.step(dpqf_col_01, np.arange(dpqf_col_01.size),
                 lw=0.6, color=clist[1] )
        axx.set_xlim( [0, 30] )
        axx.set_xlabel( 'bad (count)' )
        axx.set_ylim( [0, dpqf_col_01.size-1] )
        axx.set_ylabel( 'row' )
        axx.grid(True)

        axx = plt.subplot(gspec[1:4,2:14])
        axx.imshow( dpqf, cmap=cmap, norm=norm,
                    aspect=1, vmin=-1, vmax=10,
                    interpolation='none', origin='lower' )
        if sub_title is not None:
            axx.set_title( sub_title )

        dpqf_row_01 = np.sum( ((dpqf >= 0) & (dpqf < thres_min)), axis=0 )
        dpqf_row_08 = np.sum( ((dpqf >= 0) & (dpqf < thres_max)), axis=0 )

        axx = plt.subplot(gspec[4:6,2:14])
        axx.step(np.arange(dpqf_row_08.size), dpqf_row_08,
                 lw=0.5, color=clist[2] )
        axx.step(np.arange(dpqf_row_01.size), dpqf_row_01,
                 lw=0.6, color=clist[1] )
        axx.set_ylim( [0, 10] )
        axx.set_ylabel( 'bad (count)' )
        axx.set_xlim( [0, dpqf_row_01.size-1] )
        axx.set_xlabel( 'column' )
        axx.grid(True)

        fig_info = OrderedDict({'thres_01': low_thres})
        fig_info.update({'dpqf_01': np.sum(((dpqf >= 0) & (dpqf < thres_min)))})
        fig_info.update({'thres_08': high_thres})
        fig_info.update({'dpqf_08': np.sum(((dpqf >= 0) & (dpqf < thres_max)))})

        self.__fig_info( fig, fig_info )
        plt.tight_layout()
        self.__pdf.savefig()
        plt.close()

    # --------------------------------------------------
    def draw_signal( self, data, data_col=None, data_row=None,
                     data_label='signal', data_unit=None,
                     title=None, sub_title=None, fig_info=None ):
        '''
        Display 2D array data as image and averaged column/row signal plots

        Parameters
        ----------
        data       :  ndarray
           Numpy array (2D) holding the data to be displayed
        data_col   :  ndarray
           Numpy array (1D) column averaged values of data
           Default is calculated as biweight(data, axis=1)
        data_row   :  ndarray
           Numpy array (1D) row averaged values of data
           Default is calculated as biweight(data, axis=0)
        data_label :  string
           Name of dataset
        data_unit  :  string
           Units of dataset
        title      :  string
           Title of the figure (use attribute "title" of product)
        sub_title  :  string
           Sub-title of the figure (use attribute "comment" of product)
        fig_info   :  dictionary
           Dictionary holding meta-data to be displayed in the figure
        '''
        if data_col is None:
            data_col = np.nanmedian( data, axis=1 )

        if data_row is None:
            data_row = np.nanmedian( data, axis=0 )

        self.__frame( data, data_col, data_row, fig_info=fig_info,
                      title=title, sub_title=r'{}'.format(sub_title),
                      data_label=data_label, data_unit=data_unit )

    def draw_hist( self, signal, error,
                   data_label='signal', data_unit=None,
                   error_label='signal_std', error_unit=None,
                   title=None, sub_title=None, fig_info=None ):
        '''
        Display signal & errors as histograms

        Parameters
        ----------
        data        :  ndarray
           Numpy array (2D) holding the data to be displayed
        errors      :  ndarray
           Numpy array (2D) holding the data to be displayed
        data_label  :  string
           Name of dataset
        data_unit   :  string
           Units of dataset
        error_label :  string
           Name of dataset
        error_unit  :  string
           Units of dataset
        title       :  string
           Title of the figure (use attribute "title" of product)
        sub_title   :  string
           Sub-title of the figure (use attribute "comment" of product)
        fig_info    :  dictionary
           Dictionary holding meta-data to be displayed in the figure
        '''
        self.__hist( signal, error, fig_info,
                     title=title, sub_title=r'{}'.format(sub_title),
                     data_label=data_label, error_label=error_label,
                     data_unit=data_unit, error_unit=error_unit )

    def draw_quality( self, dpqm, title=None, sub_title=None ):
        '''
        Display pixel quality data

        Parameters
        ----------
        dpqm        :  ndarray
           Numpy array (2D) holding pixel-quality data
        title       :  string
           Title of the figure (use attribute "title" of product)
        sub_title   :  string
           Sub-title of the figure (use attribute "comment" of product)
        '''
        self.__quality( dpqm, title=title, sub_title=r'{}'.format(sub_title) )

##
## --------------------------------------------------
##
def test_frame():
    '''
    Let the user test the software!!!

    Please use the code as tutorial
    '''
    from pys5p.ocm_io import OCMio

    if os.path.isdir('/Users/richardh'):
        data_dir = '/Users/richardh/Data/proc_knmi/2015_02_23T01_36_51_svn4709_CellEarth_CH4'
    else:
        data_dir ='/nfs/TROPOMI/ocal/proc_knmi/2015_02_23T01_36_51_svn4709_CellEarth_CH4'

    icid = 31523

    # Read BAND7 product
    product_b7 = 'trl1brb7g.lx.nc'
    ocm_product = os.path.join( data_dir, 'before_strayl_l1b_val_SWIR_2',
                                product_b7 )
    # open OCAL Lx poduct
    ocm7 = OCMio( ocm_product )

    # select data of measurement(s) with given ICID
    if ocm7.select( icid ) > 0:
        dict_b7 = ocm7.get_msm_data( 'signal' )
        dict_b7_std = ocm7.get_msm_data( 'signal_error_vals' )

    # Read BAND8 product
    product_b8 = 'trl1brb8g.lx.nc'
    ocm_product = os.path.join( data_dir, 'before_strayl_l1b_val_SWIR_2',
                                product_b8 )
    # open OCAL Lx poduct
    ocm8 = OCMio( ocm_product )

    # select data of measurement(s) with given ICID
    if ocm8.select( icid ) > 0:
        dict_b8 = ocm8.get_msm_data( 'signal' )
        dict_b8_std = ocm8.get_msm_data( 'signal_error_vals' )

    # Combine band 7 & 8 data
    # del dict_b7['ICID_31524_GROUP_00000']
    # del dict_b8['ICID_31524_GROUP_00000']
    data = ocm7.dict_to_array( dict_b7, dict_b8, mode=['combine', 'median'],
                               skip_first=True, skip_last=True )
    error = ocm7.dict_to_array( dict_b7_std, dict_b8_std,
                                mode=['combine', 'median'],
                                skip_first=True, skip_last=True )

    # Generate figure
    figname = os.path.basename(data_dir) + '.pdf'
    plot = S5Pplot( figname )
    print(ocm7.get_msm_attr('signal', 'units'))
    plot.draw_signal( data,
                      data_label='signal',
                      data_unit=ocm7.get_msm_attr('signal', 'units'),
                      title=ocm7.get_attr('title'),
                      sub_title='ICID={}'.format(icid),
                      fig_info=None )
    plot.draw_hist( data, error,
                    data_label='error',
                    data_unit=ocm7.get_msm_attr('signal_error_vals', 'units'),
                    title=ocm7.get_attr('title'),
                    sub_title='ICID={}'.format(icid),
                    fig_info=None )
    del plot
    del ocm7
    del ocm8

#-------------------------
def test_ckd_dpqf():
    '''
    Let the user test the software!!!

    Please use the code as tutorial
    '''
    import h5py
    
    if os.path.isdir('/Users/richardh'):
        data_dir = '/Users/richardh/Data'
    else:
        data_dir ='/nfs/TROPOMI/ocal/ckd/ckd_release_swir/dpqf' 
    dpqm_fl = os.path.join(data_dir, 'ckd.dpqf.detector4.nc')
    
    with h5py.File( dpqm_fl, 'r' ) as fid:
        b7 = fid['BAND7/dpqf_map'][:-1,:]
        b8 = fid['BAND8/dpqf_map'][:-1,:]
        dpqm = np.hstack( (b7, b8) )

    # generate figure
    figname = 'ckd.dpqf.detector4.pdf'
    plot = S5Pplot( figname )
    plot.draw_quality( dpqm,
                       title='ckd.dpqf.detector4.nc',
                       sub_title='dpqf_map' )
    del plot
        
#-------------------------
def test_icm_dpqf():
    '''
    Let the user test the software!!!

    Please use the code as tutorial
    '''
    from pys5p.icm_io import ICMio

    if os.path.isdir('/Users/richardh'):
        data_dir = '/Users/richardh/Data/S5P_ICM_CA_SIR/001000/2012/09/18'
    elif os.path.isdir('/nfs/TROPOMI/ical/'):
        data_dir = '/nfs/TROPOMI/ical/S5P_ICM_CA_SIR/001100/2012/09/18'
    else:
        data_dir = '/data/richardh/Tropomi/ical/S5P_ICM_CA_SIR/001100/2012/09/18'
    fl_name = 'S5P_TEST_ICM_CA_SIR_20120918T131651_20120918T145629_01890_01_001100_20151002T140000.h5'
    icm_product = os.path.join(data_dir, fl_name)

    # open ICM product
    icm = ICMio( icm_product )
    if len(icm.select('DPQF_MAP')) > 0:
        res = icm.get_msm_data( 'dpqf_map' )
        dpqm = np.hstack( (res[0], res[1]) )

        res = icm.get_msm_data( 'dpqm_dark_flux' )
        dpqm_dark = np.hstack( (res[0], res[1]) )

        res = icm.get_msm_data( 'dpqm_noise' )
        dpqm_noise = np.hstack( (res[0], res[1]) )

    # generate figure
    figname = fl_name + '.pdf'
    plot = S5Pplot( figname )
    plot.draw_quality( dpqm,
                       title=fl_name,
                       sub_title='dpqf_map' )
    plot.draw_quality( dpqm_dark,
                       title=fl_name,
                       sub_title='dpqm_dark_flux' )
    plot.draw_quality( dpqm_noise,
                       title=fl_name,
                       sub_title='dpqm_noise' )
    del plot
    del icm

#--------------------------------------------------
if __name__ == '__main__':
    test_frame()
    #test_ckd_dpqf()
    #test_icm_dpqf()
