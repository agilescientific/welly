import warnings
from datetime import datetime
from io import StringIO
from urllib import error, request

import lasio
import numpy as np
import pandas as pd
from lasio import HeaderItem, CurveItem, SectionItems

from welly import utils
from welly.fields import curve_sections, other_sections, header_sections
from welly.utils import get_columns_decimal_formatter
from .fields import las_fields as LAS_FIELDS

# the lasio header item dictionary contains the fields from which we will parse
# the LASFile header metadata
header_item = HeaderItem().__dict__

# the lasio curve item dictionary contains the fields from which we will parse
# the LASFile curve header metadata
curve_item = CurveItem().__dict__

# set pandas precision higher to not automatically round the curve data
pd.set_option('precision', 10)


def from_las(file_ref, **kwargs):
    """
    Read a LAS file with lasio and parse every LAS section to a dataset that
    consists of two pd.DataFrames:
        1. curve data
        2. header metadata

    Only LAS 1.2 and 2.0 are currently supported. LAS 3.0 will be supported
    when lasio LAS 3.0 work in progress is completed:
    https://github.com/kinverarity1/lasio/issues/5.

    The design of this reader already accommodates for LAS 3.0 functionality
    where one `lasio.LASFile` can contain multiple 1D, 2D or 3D dataset
    entries, instead of only 1D data and 1 dataset in LAS 1.2 and LAS 2.0.

    Also see:
    - lasio documentation:
       https://lasio.readthedocs.io/en/latest/header-section.html#tutorial
    - LAS 3.0 file specification:
       https://www.cwls.org/wp-content/uploads/2014/09/LAS_3_File_Structure.pdf

    Args:
        file_ref (file-like object, str): either a filename, an open file
            object, or a string containing the contents of a LAS file.
        **kwargs: The additional keyword arguments are propagated to the lasio
                  reader so you can use when reading in a LAS file.
                  Find the routines of the keyword possibilities here:
                    * :func:`lasio.reader.open_with_codecs` -
                        manage issues relate to character encodings.
                    * :meth:`lasio.LASFile.read` -
                        control how NULL values and errors are handled during
                        parsing.

    Returns:
        datasets (Dict['dataset_name': (data (pd.DataFrame), header (pd.DataFrame))]):
            A dict that has an item entry for every dataset found in the LAS
            file. Any LAS dataset has a header and data part that is mapped
            1-to-1 to two separate pd.DataFrames and put into a tuple. See
            description and example below of how that is structured.

    Description of datasets object:

    datasets = {
        'Curves':   (data, header), # for LAS 1.2 & LAS 2.0
        'ASCII':    (data, header), # for LAS 3.0
        'Drilling': (data, header), # for LAS 3.0
        'Core[1]':  (data, header), # for LAS 3.0 - Run 1
        'Core[2]':  (data, header)  # for LAS 3.0 - Run 2
    }

    Where:
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
    Example
    --------
    >> datasets = from_las(path)

    >> datasets['Curves'][0]
         DEPT    CALI     FACIES
    0    1.0     2.4438   0
    1    1.5     2.4438   1
    2    2.0     2.4438   2

    >> datasets['Curves'][1]
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
    # read las file with lasio
    las = lasio.read(file_ref, **kwargs)

    # parse lasio.LASFile object to datasets dictionary
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
            warnings.warn(f"Warning, LAS version {version} not yet supported. "
                          "Attempting to use LAS 1.2 and 2.0 parsing logic "
                          "for LAS 3.0.")
            datasets = from_las_2_or_older(las)
        except Exception:
            raise NotImplementedError(
                f"LAS version {version} not yet supported.")

    return datasets


def from_las_2_or_older(las):
    """
    Parse `lasio.LASFile` (LAS version 1.2 & 2.0) to two `pd.DataFrames` that
    form 1 `datasets` entry as a tuple.

    Requires: LASFile version 1.2 or 2.0.

    For LAS versions 1.2 & 2.0, one LAS file translates to one `Curves` dataset

    Args:
        las (lasio.LASFile): `LASFile` constructed through `lasio.read()`

    Returns:
        datasets (Dict['Curves': (data, header)]):
            Dictionary with one item that maps dataset name (`Curves`) to a
            tuple with `data` & `header` objects.

        Where:
            data   (pd.DataFrame): curve data
            header (pd.DataFrame): well and curve header metadata
    """
    # construct df to parse data sections to
    data = pd.DataFrame()

    # construct df to parse header sections to
    header = pd.DataFrame()

    # parse header from LASFile to df
    for section, item_list in las.sections.items():

        # section composed of SectionItem instance(s)
        if section in header_sections:
            # construct df
            df_section = pd.DataFrame(
                [i.__dict__ for i in las.sections[section]])
            # append section name as separate column
            df_section['section'] = section
            # concat metadata to header df
            header = pd.concat([header, df_section])

            # section is also composed of CurveItem instance(s)
            if section in curve_sections:
                if len(las.sections[section]) > 0:
                    # construct df
                    df_section = pd.DataFrame(
                        [i.__dict__ for i in las.sections[section]])
                    # parse curve data to separate df
                    df_section = pd.DataFrame(
                        np.matrix(df_section.data.tolist()).transpose(),
                        columns=df_section.mnemonic.values)
                    # concat to curve data df
                    data = pd.concat([data, df_section])
                    # all Curves are parsed as strings if there is a string
                    for column in data.columns:
                        if data[column].dtype == 'O':
                            # replacement of string null values with np.nan
                            data[column] = data[column].replace(
                                str(las.well["NULL"].value), np.nan)
                            data[column] = data[column].replace(
                                str(las.well["NULL"].value) + '.0', np.nan)
                            try:
                                # convert numeric Curves to floats
                                data[column] = data[column].astype(np.float64)
                            except ValueError:
                                pass

        # section is a Str instance
        elif section in other_sections:
            # fill other section in descr key of header item dictionary
            header_item['descr'] = item_list
            # construct dataframe for 'Other' section
            df_section = pd.DataFrame(header_item, index=[0])
            # append section name as separate column
            df_section['section'] = section
            # concat to header df
            header = pd.concat([header, df_section])

        else:
            warnings.warn(
                'This section was not recognized and therefore not parsed: '
                '"{}"'.format(section))

    header.drop(['data'], axis=1, inplace=True)

    return {'Curves': (data, header)}


def datasets_to_las(path, datasets, **kwargs):
    """
    Write datasets to a LAS file on disk.

    Args:
        path (Str): Path to write LAS file to
        datasets (Dict['dataset_name': (data (pd.DataFrame), header (pd.DataFrame))]):
            Datasets with data & header

    Returns:
        Nothing, only writes in-memory object to disk as .las
    """
    # ensure path is working on every dev set-up
    path = utils.to_filename(path)

    # instantiate new LASFile to parse data & header to
    las = lasio.LASFile()

    # unpack datasets
    for dataset, (data, header) in datasets.items():

        if dataset == 'Curves':
            # parse header pd.DataFrame to LASFile
            for section_name in set(header.section.values):

                # get header section
                df_section = header[header.section == section_name]

                if section_name == 'Version':
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

                elif section_name == 'Curves':
                    for i, header_row in df_section.iterrows():
                        if header_row.mnemonic in data.columns:
                            curve_data = data.loc[:, header_row.mnemonic]
                            las.append_curve(mnemonic=header_row.mnemonic,
                                             data=curve_data,
                                             unit=header_row.unit,
                                             descr=header_row.descr,
                                             value=header_row.value)

                elif section_name == 'Other':
                    las.sections["Other"] = df_section['descr'][0]

                else:
                    warnings.warn('Section was not recognized and not parsed: '
                                  '"{}"'.format(section_name))
        else:
            # TODO: Investigate how we parse LAS3 datasets
            # ~Ascii or ~Log ~Core ~Inclinometry ~Drilling ~Tops ~Test
            raise NotImplementedError('LAS 3.0 is not yet supported.')

        # numeric null value representation from the header (e.g. # -9999)
        try:
            null_value = header[header.original_mnemonic == 'NULL'].value.iloc[0]
        except IndexError:
            null_value = None

        # las.write defaults to %.5 decimal points. We want to retain the
        # number of decimals. We first construct a column formatter based on
        # the max number of decimal points found in each curve.
        if 'column_fmt' not in kwargs:
            kwargs['column_fmt'] = get_columns_decimal_formatter(
                data=las.data, null_value=null_value)

        # write file to disk
        with open(path, mode='w') as f:
            las.write(f, **kwargs)


def to_lasio(well, keys=None, alias=None, basis=None, null_value=-999.25):
    """
    Constructor. If you have a `well` object, this will create a
    `lasio.LASFile` object from it.

    Args:
        keys (list): List of strings: the keys of the data items to
            include, if not all of them. You can have nested lists, such
            as you might use for ``tracks`` in ``well.plot()``.
        alias (dict): Optional. A dictionary alias for the curve mnemonics.
        basis (numpy.ndarray): Optional. The basis to export the curves in.
            If you don't specify one, it will survey all the curves with
            `survey_basis()``.
        null_value (float): Optional. The null value representation in the
            LAS file.

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
                df = getattr(well, obj)
                # get item value from df
                try:
                    value = df[df.mnemonic == item].value.iloc[0]
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

    # Add a depth basis.
    if basis is None:
        basis = well.survey_basis(keys=keys, alias=alias)
    try:
        l.add_curve('DEPT', basis)
    except:
        raise Exception("Please provide a depth basis.")

    # Add meta from basis.
    setattr(l.well, 'STRT', basis[0])
    setattr(l.well, 'STOP', basis[-1])
    setattr(l.well, 'STEP', basis[1] - basis[0])

    # Add data entities.
    other = ''

    keys = well._get_curve_mnemonics(keys, alias=alias)

    for k in keys:
        d = well.data[k]
        # if getattr(d, 'null', None) is not None:
        #     d[np.isnan(d)] = d.null
        try:
            new_data = np.copy(d.to_basis_like(basis))
        except:
            # Basis shift failed; is probably not a curve
            pass
        try:
            descr = getattr(d, 'description', '')
            l.add_curve(k.upper(), new_data, unit=d.units, descr=descr)
        except:
            try:
                # Treat as OTHER
                other += "{}\n".format(k.upper()) + d.to_csv()
            except:
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
