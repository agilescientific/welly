import lasio
import numpy as np
import pandas as pd
from lasio import HeaderItem, CurveItem, SectionItems
import warnings

from welly import utils
from welly.fields import curve_sections, other_sections, header_sections
from welly.utils import get_columns_decimal_formatter

# the lasio header item dictionary contain the fields from which we will parse the LASFile header metadata
header_item = HeaderItem().__dict__

# the lasio curve item dictionary contain the fields from which we will parse the LASFile curve header metadata
curve_item = CurveItem().__dict__

# set pandas precision higher than the default of 5 so that it will not automatically round off the curve data
pd.set_option('precision', 10)


def from_las(path, **kwargs):
    """
    Read LAS file with lasio and parse every LAS dataset to 2 pd.DataFrames:
        1. curve data
        2. header metadata

    Only LAS 1.2 and 2.0 are currently supported. LAS 3.0 will be supported when lasio LAS 3.0 work is finished:
    https://github.com/kinverarity1/lasio/issues/5. The design of this reader already accommodates for LAS 3.0
    functionality where 1 lasio.LASFile can contain multiple 1D, 2D or 3D dataset entries. Also see lasio documentation:
    https://lasio.readthedocs.io/en/latest/header-section.html#tutorial

    Args:
        path (str): Path to LAS file
        **kwargs: The additional keyword arguments are propagated to the lasio reader so you can use when reading in a
                  LAS file. Find the routines of the different keyword possibilities look here:
                    * :func:`lasio.reader.open_with_codecs` - manage issues relate to character encodings
                    * :meth:`lasio.LASFile.read` - control how NULL values and errors are handled during parsing

    Returns:
        datasets (Dict['dataset_name': (data (pd.DataFrame), header (pd.DataFrame))]):
            A dict that has an item for every dataset found in the LAS file. Any LAS dataset has a header and data part
            that is mapped 1-to-1 to two separate pd.DataFrames and put into a tuple. See below for an example of how
            that is structured.


    Example of how a return would be structured:

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
                                - every column represents a data variable. Column name is the data variable mnemonic.
        header (pd.DataFrame): where:
                                - every row represents a line read from LAS file and columns.
                                - column 1-5 - directly parsed from the HeaderItem.__dict__:
                                    'original_mnemonic' - original mmnemonic
                                    'mnemonic' - mnemonic
                                    'unit' - unit
                                    'value' - value
                                    'descr' - description
                                - column 6 - is added as an identifier to track of sections:
                                    'section' (str) - Section name the line from the LAS file belongs to.

        Example of how returns of a 'data' and 'header' object would look:

        data = pd.DataFrame({
            'DEPT': [100.0, 101.0, 102.0],
            'GR': [80.0, 85.0, 82.0],
            'DEN': [2.10, 2.15, 2.20]
        })

        header = pd.DataFrame({
            'original_mnemonic': ['VERS', 'WRAP', 'STRT', 'STOP', 'STEP', 'DEPT', 'GR', 'DEN', ''],
            'mnemonic': ['VERS', 'WRAP', 'STRT', 'STOP', 'STEP', 'DEPT', 'GR', 'DEN', ''],
            'unit': ['', '', 'M', 'M', 'M', 'M', 'GAPI', 'g/cm3', '']
            'value': [2.0, 'NO', 100.0, 102.0, 1.0, '', '', '', '']
            'descr': ['Version 2.0', 'One line per depth step', '', '', '', 'DEPTH', 'Gamma Ray', 'Density', 'Comment']
            'section': ['Version', 'Version', 'Well', 'Well', 'Well', 'Curves', 'Curves', 'Curves', 'Other']
        })
    """
    # read las file
    las = lasio.read(path, **kwargs)

    # get las format version
    version = float(las.version[0].value)

    if version == 2.0 or version == 1.2:
        datasets = from_las2(las)
    else:
        try:
            datasets = from_las2(las)
            warnings.warn(f"Warning, LAS version {version} not yet supported. "
                          "Attempting to use LAS<=2.0 parsing logic for LAS3.0.")
        except Exception:
            raise NotImplementedError(f"LAS version {version} not yet supported")

    return datasets


def from_las2(las):
    """
    Parse lasio.LASFile (LAS version 1.2 & 2.0) to 2 pd.DataFrames that form 1 datasets entry as a tuple.

    For LAS versions 1.2 & 2.0, 1 LAS file translates to 'Curves' 1 data set.

    Args:
        las (lasio.LASFile): LASFile constructed through lasio.read()

    Returns:
        datasets = {'Curves': (data, header)}

        data   (pd.DataFrame): df where:
                                - indexed by order of vertical occurrence in las file.
                                - every row represents a data index.
                                - every column represents a data variable. Column name is the data variable mnemonic.
        header (pd.DataFrame): df where every row represents a line read from LAS file and columns:
                                - column 1-5 - directly parsed from the HeaderItem where attributes are columns:
                                    'original_mnemonic' - original mmnemonic
                                    'mnemonic' - mnemonic
                                    'unit' - unit
                                    'value' - value
                                    'descr' - description
                                - column 6 - is added as an identifier to know which las section the row belongs to:
                                    'section' (str) - section name the line from the LAS file belongs to.
    Example:

    datasets = {'Curves': (data, header))

    data = pd.DataFrame({
        'DEPT': [100.0, 101.0, 102.0],
        'GR': [80.0, 85.0, 82.0],
        'DEN': [2.10, 2.15, 2.20]
    })

    header = pd.DataFrame({
        'original_mnemonic': ['VERS', 'WRAP', 'STRT', 'STOP', 'STEP', 'DEPT', 'GR', 'DEN', ''],
        'mnemonic': ['VERS', 'WRAP', 'STRT', 'STOP', 'STEP', 'DEPT', 'GR', 'DEN', ''],
        'unit': ['', '', 'M', 'M', 'M', 'M', 'GAPI', 'g/cm3', '']
        'value': [2.0, 'NO', 100.0, 102.0, 1.0, '', '', '', '']
        'descr': ['Version 2.0', 'One line per depth step', '', '', '', 'DEPTH', 'Gamma Ray', 'Density', 'Comment']
        'section': ['Version', 'Version', 'Well', 'Well', 'Well', 'Curves', 'Curves', 'Curves', 'Other']
    })
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
            df_section = pd.DataFrame([i.__dict__ for i in las.sections[section]])
            # append section name as separate column
            df_section['section'] = section
            # concat metadata to header df
            header = pd.concat([header, df_section])

            # section is also composed of CurveItem instance(s)
            if section in curve_sections:
                if len(las.sections[section]) > 0:
                    # construct df
                    df_section = pd.DataFrame([i.__dict__ for i in las.sections[section]])
                    # parse curve data to separate df
                    df_section = pd.DataFrame(np.matrix(df_section.data.tolist()).transpose(),
                                              columns=df_section.mnemonic.values)
                    # concat to curve data df
                    data = pd.concat([data, df_section])
                    # all curves are parsed as strings if there is one string present somewhere
                    for column in data.columns:
                        if data[column].dtype == 'O':
                            # replacement of string null values with np.nan
                            data[column] = data[column].replace(str(las.well["NULL"].value), np.nan)
                            data[column] = data[column].replace(str(las.well["NULL"].value) + '.0', np.nan)
                            try:
                                # attempt to convert numeric curves to float type
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
            warnings.warn('This section was not recognized and therefore not parsed: "{}"'.format(section))

    header.drop(['data'], axis=1, inplace=True)

    return {'Curves': (data, header)}


def to_las(path, datasets, **kwargs):
    """
    Write datasets to a LAS file.

    Args:
        path (Str): Path to write LAS file to
        datasets (Dict['dataset_name': (data (pd.DataFrame), header (pd.DataFrame))]): Data sets with data & headers

    Return:
        Nothing, only writes in-memory object to disk.
    """
    # ensure path is working on every dev set-up
    path = utils.to_filename(path)

    # instantiate new LASFile to parse data and header to
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
                        [HeaderItem(r.original_mnemonic, r.unit, r.value, r.descr) for i, r in df_section.iterrows()])

                elif section_name == 'Parameter':
                    las.sections["Parameter"] = SectionItems(
                        [HeaderItem(r.original_mnemonic, r.unit, r.value, r.descr) for i, r in df_section.iterrows()])

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
                    warnings.warn('Section was not recognized and not parsed: "{}"'.format(section_name))
        else:
            raise NotImplementedError('LAS 3.0 is not yet supported.')

        # get the numeric null value representation if it exists in the header (e.g. -9999)
        try:
            null_value = header[header.original_mnemonic == 'NULL'].value.iloc[0]
        except IndexError:
            null_value = None

        # las.write defaults to %.5 decimal points where we would like to retain the number of decimals
        # therefore we first construct a column formatter based on  the max number of decimal points found in each curve
        if not 'column_fmt' in kwargs:
            kwargs['column_fmt'] = get_columns_decimal_formatter(data=las.data, null_value=null_value)

        # write file to disk
        with open(path, mode='w') as f:
            las.write(f, **kwargs)
