"""
Module for reading and writing to and from LAS files

:copyright: 2021 Agile Scientific
:license: Apache 2.0
"""
from functools import reduce
import warnings
from datetime import datetime
from io import StringIO
from urllib import error, request

import lasio
import numpy as np
import pandas as pd
from lasio import HeaderItem, CurveItem, SectionItems
from pandas._config.config import OptionError

from welly.curve import Curve
from welly import utils
from welly.fields import curve_sections, other_sections, header_sections
from welly.utils import get_columns_decimal_formatter, get_step_from_array
from .fields import las_fields as LAS_FIELDS

# the lasio header item dictionary contains the fields from which we will parse
# the LASFile header metadata
header_item = HeaderItem().__dict__

# the lasio curve item dictionary contains the fields from which we will parse
# the LASFile curve header metadata
curve_item = CurveItem().__dict__

# set pandas precision higher to not automatically round the curve data
try:
    pd.set_option('precision', 10)
except:
    # python >= 3.8
    pd.set_option('display.precision', 10)


def from_las(file_ref, **kwargs):
    """
    Read a LAS file with lasio and parse every LAS section to a dataset that
    consists of two pd.DataFrames:

        1. curve data
        2. header metadata

    Only LAS 1.2 and 2.0 are currently supported. LAS 3.0 will be supported
    when lasio LAS 3.0 work in progress is completed:

        - https://github.com/kinverarity1/lasio/issues/5.

    The design of this reader already accommodates for LAS 3.0 functionality
    where one `lasio.LASFile` can contain multiple 1D, 2D or 3D dataset
    entries, instead of only 1D data and 1 dataset in LAS 1.2 and LAS 2.0.

    Also see:

        - lasio documentation: https://lasio.readthedocs.io/en/latest/header-section.html#tutorial
        - LAS 3.0 file specification: https://www.cwls.org/wp-content/uploads/2014/09/LAS_3_File_Structure.pdf

    Args:
        file_ref (file-like object, str): either a filename, an open file
            object, or a string containing the contents of a LAS file.
        **kwargs: The additional keyword arguments are propagated to the lasio
            reader so you can use when reading in a LAS file.
            Find the routines of the keyword possibilities here:

            * ``lasio.reader.open_with_codecs`` -
                manage issues relate to character encodings.
            * ``lasio.LASFile.read`` -
                control how NULL values and errors are handled during
                parsing.

    Returns:
        datasets (Dict['<name>': pd.DataFrame]): Dictionary maps a
            dataset name (e.g. 'Curves') or 'Header' to a pd.DataFrame.

    Description of datasets object:

        datasets = {
            'Curves':   data,   # for LAS 1.2 & LAS 2.0
            'ASCII':    data,   # for LAS 3.0
            'Drilling': data,   # for LAS 3.0
            'Core[1]':  data,   # for LAS 3.0 - Run 1
            'Core[2]':  data,   # for LAS 3.0 - Run 2
            'Header':   header, # for all (LAS 1.2, LAS 2.0, LAS 3.0)
        }

    Where...
        data (pd.DataFrame):   where:

            - every row represents a data index.
            - every column represents a data variable.
              Column name is the data variable mnemonic.

        header (pd.DataFrame): where:

            - every row represents a line read from LAS
              file and columns.
            - column 1-5 - directly parsed from the
                           HeaderItem.__dict__:
                'original_mnemonic' - original mmnemonic
                'mnemonic' - mnemonic
                'unit' - unit
                'value' - value
                'descr' - description
            - column 6 - is added as a LAS section
                         identifier:
                'section' (str) - LAS Section name the
                line from the LAS file belongs to (e.g.
                ~Curves)

    Example:
        >>> datasets = from_las(path)
        >>> datasets['Curves']
             DEPT    CALI     FACIES
        0    1.0     2.4438   0
        1    1.5     2.4438   1
        2    2.0     2.4438   2
        >>> datasets['Header']
            original_mnemonic   mnemonic unit  value    descr         section
        0   VERS                VERS           2.0                    Version
        1   WRAP                WRAP           YES                    Version
        0   STRT                STRT     M     1.0668   START DEPTH   Well
        1   STOP                STOP     M     1.524    STOP DEPTH    Well
        2   STEP                STEP     M     0.1524   STEP          Well
        3   NULL                NULL           -999.25  NULL VALUE    Well
        4   COMP                COMP           Energy.C COMPANY       Well
        5   WELL                WELL                    WELL          Well
        6   UWI                 UWI                     WELL          Well
        7   FLD                 FLD                     FIELD         Well
        0   DEPT                DEPT     m              DEPTH         Curves
        1   CALI                CALI     in             Caliper       Curves
        2   FACIES              FACIES                  Facies        Curves
        2   EREF                EREF:1   M     100.0    Elevation     Parameter
        0                       UNKNOWN                 Comment       Other
    """
    # Read las file with lasio.
    las = lasio.read(file_ref, **kwargs)

    # Parse lasio.LASFile object to datasets dictionary.
    datasets = from_lasio(las)

    return datasets


def from_lasio(las):
    """
    Creates a datasets dictionary object from a `lasio.LASFile`.

    Args:
        las (lasio.LASFile): `LASFile` constructed through `lasio.read()`

    Returns:
        datasets = {'Curves': (data, header)}
    """
    # get las format version
    version = get_las_version(las)

    if version == 2.0 or version == 1.2:
        datasets = from_las_2_or_older(las)
    else:
        try:
            m = f"Warning, LAS version {version} not yet supported. " \
                f"Attempting to use LAS 1.2 and 2.0 parsing logic for LAS 3.0."
            warnings.warn(m, stacklevel=2)
            datasets = from_las_2_or_older(las)
        except Exception:
            raise NotImplementedError(
                f"LAS version {version} not yet supported.")

    return datasets


def from_las_2_or_older(las):
    """
    Parse `lasio.LASFile` to two `pd.DataFrames`. The 'Header' and 'Curves'
    section translate both to a `pd.DataFrame`.

    Requires: LASFile version 1.2 or 2.0.

    Args:
        las (lasio.LASFile): `LASFile` constructed through `lasio.read()`

    Returns:
        datasets (Dict['<name>': pd.DataFrame]): Dictionary maps a
            dataset name (e.g. 'Curves') or 'Header' to a pd.DataFrame.
    """
    datasets = {}

    # construct df to parse header sections to
    header = pd.DataFrame()

    # parse header from LASFile to df
    for section, item_list in las.sections.items():
        # skip section if item list is empty and not an `Other` section
        if len(item_list) == 0 and not isinstance(item_list, str):
            continue

        # section contains `SectionItem` instance(s)
        elif section.casefold() in [s.casefold() for s in header_sections]:
            # construct df for LAS section
            df_section = pd.DataFrame([i.__dict__ for i in las.sections[section]])
            # append section name as a separate column
            df_section['section'] = section
            # concat metadata to header df
            header = pd.concat([header, df_section])

            # section is also contains `CurveItem` instance(s)
            if section.casefold() in [s.casefold() for s in curve_sections]:
                # get and append data df to datasets
                datasets[section] = _get_curve_las_df(las, section)

        # section contains only `CurveItem` instance(s)
        elif section.casefold() in [s.casefold() for s in curve_sections]:
            # get and append data df to datasets
            datasets[section] = _get_curve_las_df(las, section)

        # section is a string instance
        elif section.casefold() in [s.casefold() for s in other_sections]:
            # fill other section in descr key of header item dictionary
            header_item['descr'] = item_list
            # construct dataframe for 'Other' section
            df_section = pd.DataFrame(header_item, index=[0])
            # append section name as separate column
            df_section['section'] = section
            # concat to header df
            header = pd.concat([header, df_section])

        else:
            m = f'Section was not recognized and not parsed: {section}'
            warnings.warn(m, stacklevel=2)

    header.drop(['data'], axis=1, inplace=True)

    header.reset_index(drop=True, inplace=True)

    datasets['Header'] = header

    return datasets


def datasets_to_las(path, datasets, **kwargs):
    """
    Write datasets to a LAS file on disk.

    Args:
        path (Str): Path to write LAS file to
        datasets (Dict['<name>': pd.DataFrame]): Dictionary maps a
            dataset name (e.g. 'Curves') or 'Header' to a pd.DataFrame.

    Returns:
        Nothing, only writes in-memory object to disk as .las
    """
    # ensure path is working on every dev set-up
    path = utils.to_filename(path)

    # instantiate new LASFile to parse data & header to
    las = lasio.LASFile()

    # set header df as variable to later retrieve curve meta data from
    header = datasets['Header']

    # unpack datasets
    for dataset_name, df in datasets.items():

        # dataset is the header
        if dataset_name == 'Header':
            # parse header pd.DataFrame to LASFile
            for section_name in set(df.section.values):
                # get header section df
                df_section = df[df.section == section_name]

                if section_name == 'Curves':
                    # curves header items are handled in curve data loop
                    pass

                elif section_name == 'Version':
                    if len(df_section[df_section.original_mnemonic == 'VERS']) > 0:
                        las.version.VERS = df_section[df_section.original_mnemonic == 'VERS']['value'].values[0]
                    if len(df_section[df_section.original_mnemonic == 'WRAP']) > 0:
                        las.version.WRAP = df_section[df_section.original_mnemonic == 'WRAP']['value'].values[0]
                    if len(df_section[df_section.original_mnemonic == 'DLM']) > 0:
                        las.version.DLM = df_section[df_section.original_mnemonic == 'DLM']['value'].values[0]

                elif section_name == 'Well':
                    las.sections["Well"] = SectionItems(
                        [HeaderItem(r.original_mnemonic,
                                    r.unit,
                                    r.value,
                                    r.descr) for i, r in df_section.iterrows()])

                elif section_name == 'Parameter':
                    las.sections["Parameter"] = SectionItems(
                        [HeaderItem(r.original_mnemonic,
                                    r.unit,
                                    r.value,
                                    r.descr) for i, r in df_section.iterrows()])

                elif section_name == 'Other':
                    las.sections["Other"] = df_section['descr'].iloc[0]

                else:
                    m = f"LAS Section was not recognized: '{section_name}'"
                    warnings.warn(m, stacklevel=2)

        # dataset contains curve data
        if dataset_name in curve_sections:
            header_curves = header[header.section == dataset_name]
            for i, header_row in header_curves.iterrows():
                if header_row.mnemonic in df.columns:
                    curve_data = df.loc[:, header_row.mnemonic]
                    las.append_curve(mnemonic=header_row.mnemonic,
                                     data=curve_data,
                                     unit=header_row.unit,
                                     descr=header_row.descr,
                                     value=header_row.value)

    # numeric null value representation from the header (e.g. # -9999)
    try:
        null_value = header[header.original_mnemonic == 'NULL'].value.iloc[0]
    except IndexError:
        null_value = None

    # las.write defaults to %.5 decimal points. We want to retain the
    # number of decimals. We first construct a column formatter based
    # on the max number of decimal points found in each curve.
    if 'column_fmt' not in kwargs:
        kwargs['column_fmt'] = get_columns_decimal_formatter(
            data=las.data, null_value=null_value)

    # write file to disk
    with open(path, mode='w') as f:
        las.write(f, **kwargs)


def to_lasio(well,
             keys=None,
             alias=None,
             basis=None,
             null_value=-999.25,
             mnemonic_case='preserve',
             ):
    """
    Constructor. If you have a `well` object, this will create a
    `lasio.LASFile` object from it.

    Args:
        keys (list): List of strings: the keys of the data items to
            include, if not all of them. You can have nested lists, such
            as you might use for ``tracks`` in ``well.plot()``.
        alias (dict): Optional. A dictionary alias for the curve mnemonics.
                e.g. {'density': ['DEN', 'DENS']}
        basis (numpy.ndarray): Optional. The basis to export the curves in.
            If you don't specify one, it will survey all the curves with
            `survey_basis()``.
        null_value (float): Optional. The null value representation in the
            LAS file.
        mnemonic_case (str): Optional. Can be 'upper', 'lower', 'title',
            or 'preserve'. Default: 'preserve'.

    Returns:
        las (lasio.LASFile). The lasio object representation of a LAS file.
    """
    # Create an empty lasio object.
    l = lasio.LASFile()
    l.well.DATE = str(datetime.today())
    l.well["NULL"].value = null_value

    # Deal with header.
    for obj, dic in LAS_FIELDS.items():
        if obj == 'header':
            for attr, (sect, item) in dic.items():
                df_header = getattr(well, obj)
                # get item value from header dataframe
                try:
                    value = df_header[df_header.mnemonic == item].value.iloc[0]
                except IndexError:
                    value = None
                # set item value on LASFile instance
                try:
                    getattr(l, sect)[item].value = value
                except KeyError:
                    h = lasio.HeaderItem(item, "", value, "")
                    getattr(l, sect)[item] = h
        elif obj == 'location':
            for attr, (sect, item) in dic.items():
                value = getattr(getattr(well, obj), attr, None)
                try:
                    getattr(l, sect)[item].value = value
                except KeyError:
                    h = lasio.HeaderItem(item, "", value, "")
                    getattr(l, sect)[item] = h
        else:
            pass

    # Clear curves from header portion.
    l.header['Curves'] = []

    # Put all curve dfs in a list, if possible.
    # TODO: This needs to handle striplogs as well, but striplogs
    # do not have a .df attribute.
    dfs = [curve.df for curve in well.data.values() if isinstance(curve, Curve)]

    # Deal with data if available:
    if len(dfs) > 0:
        # Merge all curve dfs to one df.
        df_merged = reduce(lambda left, right: pd.merge(left,
                                                        right,
                                                        left_index=True,
                                                        right_index=True), dfs)

        # Get the mnemonics to select.
        keys = well._get_curve_mnemonics(keys, alias=alias)

        df_merged = df_merged[keys]

        if basis:
            df_merged = df_merged.reindex(basis)
        try:
            l.add_curve('DEPT', df_merged.index.values)
        except:
            raise Exception("Please provide an index.")

        # Add meta from basis.
        setattr(l.well, 'STRT', df_merged.index[0])
        setattr(l.well, 'STOP', df_merged.index[-1])
        setattr(l.well, 'STEP', get_step_from_array(df_merged.index.values))

    # Add data entities.
    other = ''

    keys = well._get_curve_mnemonics(keys, alias=alias)

    for key in keys:
        # select curve from well
        curve = well.data[key]

        if isinstance(curve, Curve):
            # iterate over columns for 2D curve data
            for col in curve.df.columns:
                case = {
                    'upper': str.upper,
                    'lower': str.lower,
                    'title': str.title,
                    'preserved': str,
                }
                key_ = case.get(mnemonic_case, str)(key)
                try:
                    # take the series, reindex it and transform to np.array
                    new_data = curve.df[col].reindex(basis).values
                    descr = getattr(curve, 'description', '')
                    l.add_curve(mnemonic=key_,
                                data=new_data,
                                unit=curve.units,
                                descr=descr)
                except:
                    # appending curve failed, add to OTHER section
                    
                    other += "{}\n".format(key_) + curve.to_csv()
        else:
            pass

    # Write OTHER, if any.
    if other:
        l.other = other

    return l


def file_from_url(url):
    """
    Retrieve a file from an HTTPS URL and return it as an in-memory stream
    for text.

    Args:
        url (str): URL to file.

    Returns:
        text_file (StringIO): an in-memory stream for text.
    """
    try:
        text_file = StringIO(request.urlopen(url).read().decode())
    except error.HTTPError as e:
        raise Exception('Could not retrieve url: ', e)

    return text_file


def get_las_version(las):
    """
    Get the LAS file format version from an in-memory lasio.LAFile object.

    There are 3 possible versions (https://www.cwls.org/products/):

        - LAS 1.2
        - LAS 2.0
        - LAS 3.0

    Args:
        las (lasio.LASFile): An in-memory lasio.LASFile object

    Returns:
        version (float): LAS format version
    """
    version = float(las.version[0].value)

    return version


def _get_curve_las_df(las, section):
    """
    Get the curve dataframe.
    """
    # construct df
    df_section = pd.DataFrame([i.__dict__ for i in las.sections[section]])

    if df_section.empty:
        return None
    else:
        # parse curve data to separate df
        data = pd.DataFrame(np.array(df_section.data.tolist()).transpose(),
                            columns=df_section.mnemonic.values)

        # all curves are parsed as strings if there is a string
        for column in data.columns:
            if data[column].dtype == 'O':
                # replace string null values with np.nan
                data[column] = data[column].replace(
                    str(las.well["NULL"].value), np.nan)
                data[column] = data[column].replace(
                    str(las.well["NULL"].value) + '.0', np.nan)
                try:
                    # try to convert numeric curve values to floats
                    data[column] = data[column].astype(np.float64)
                except ValueError:
                    pass
        return data
