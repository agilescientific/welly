# Changelog

## 0.5.2rc0, 23 February 2022

- Fixed [bug #208](https://github.com/agile-geoscience/welly/issues/208) which essentially meant `rename_alias` was always `False` when getting a well or project as a DataFrame.

## 0.5.1, 18 February 2022

- `Curve.values` now returns a 1D array for a 1D curve.
- Added `Project.basis_range` to provide the min and max of all curves in the project.
- Added [a user guide page for `Project`](https://code.agilescientific.com/welly/userguide/projects.html).
- Fixed [bug #202](https://github.com/agile-geoscience/welly/issues/202) with curve indexing.
- Fixed [bug #206](https://github.com/agile-geoscience/welly/issues/206) that prevented quality tests from running on aliased curves.
- Fixed [bug #207](https://github.com/agile-geoscience/welly/issues/207) that was causing the quality table not to render correctly in some situations.

## 0.5.0, 14 February 2022

- Major change: Everything in `welly` is now much closer to `pandas`. Chiefly, `Curve` objects are now represented by wrapped `pandas.DataFrame` objects (note: not `Series` as you might expect, so they can be two-dimensional). They were previously subclassed NumPy `ndarray` objects, so while we've tried to preserve as much of the API as possible, expect some changes. Please let us know if there's something you miss, it can probably be implemented. Many thanks to the developers that made this happen, especially Patrick Reinhard and Wenting Xiong in the Netherlands.
- Major change: as previously indicated, the default behaviour is now to load the depth curve in its original units. That is: `welly` no longer converts everything to metres. Use `index='metres'` in `from_las()` to get the old behaviour.
- Major change: the `Well` object's header, `well.header`, is currently a large `pandas.DataFrame` containing everything from the LAS file's header. In the next minor release, we will restore something more like the original header object. We welcome opinions on how this should work.
- The `Curve` object should be instantiated with `index` instead of `basis`.
- You can now create a project with `welly.read_las('path/to/*.las')`. Note: this always gives you a project, even if it only contains a single well. You can get the single well from a path like `'data/myfile.las'` with a singleton assignment like `well, = welly.read_las('data/myfile.las')`.
- As previously indicated, dogleg severity is now given in units of degrees per course length.
- `kwargs` are passed to `lasio` in `read_las()`, `Well.from_las()` and `Project.from_las()`, so you can add things like `mnemonic_case='preserve'` or `ignore_header_errors=True`. See [the Lasio documentation](https://lasio.readthedocs.io/en/latest/) for more on these options.
- A new argument on `well.to_las()` allows you to control the case of the mnemonics in the output LAS file. The behaviour has always been to preserve the case in the data dictionary; choose 'upper', 'title' or 'lower' to change it.
- New docs! They are live at [code.agilescientific.com/welly](https://code.agilescientific.com/welly). Feedback welcome!


## 0.4.10, 22 June 2021

- No longer supporting versions of Python before 3.6.
- `Curve.top_and_tail()` has been implemented. It removes NaNs from the start and end — but not the middle — of a log.
- You can now optionally pass any of `start`, `stop` and `step` to `Well.unify_basis()`. These settings will override the basis you provide, or the basis that `welly` discovers using `Well.survey_basis()`. I added an example of using this to the `tutorial/02_Curves.iynb` tutorial notebook.
- Relatedly, if you pass any of `start`, `stop` and `step` to `Curve.to_basis()` it will _override_ the basis you give it, if you give it one.
- Welly now uses [`wellpathpy`](https://github.com/Zabamund/wellpathpy) to convert deviation data into a position log. The API has not changed, but position logs can now be calculated with the high and low tangential methods as well.
- Dogleg severity is still given in radians, but can be normalized per 'course length', where course length is a parameter you can pass. **Future warning:** from v0.5.0, dogleg severity will be passed in degrees and course length will be 30 by default.


## 0.4.9, 29 January 2021

- Fixed a bug that was preventing Alias names from appearing in the DataFrame view, `project.df()` and `well.df`. Updated the `Project` tutorial to reflect this.
- Fixed a bug that was preventing Aliases from applying properly to well plots.
- Improved the error you get fro `w.plot(tracks=[...])` if there are no curves to plot (e.g. if none of the names exist).


## 0.4.8, 11 December 2020

- Reorganized the `tutorials` a bit and made sure they all run as-is.
- A new `Location.from_petrel()` function accepts a Petrel `.dev` deviation file. It will extract the x and y location, and the KB, as well as the position log and/or deviation survey.
- `Curve.plot_2d()` now handles NaNs in the curve.
- The test functions now accept a `keys` argument to limit the number of items the tests will be applied to, or to order the appearance of curves in `qc_table_html`. For example, if you pass `keys=['GR']` then tests will only be run on `w.data['GR']`, regardless of what's in the `tests` dictionary. This was [issue #104](https://github.com/agile-geoscience/welly/issues/104).
- You can now pass a `pathlib.Path` object to `from_las`. Thank you to Kent Inverarity for implementing this feature.
- Added `XCOORD` and `YCOORD` as standard fields; these are read in as `location.x` and `location.y` repsectively.
- Added `Project.plot_map()` to make a quick (ugly) scatter plot from x and y location (whatever two field you provide from the `location` object).
- Added the `filter_wells_by_data()` method to `Project`, and deprecated `find_wells_with_curve()` and `find_wells_without_curve()`. You can make complex selections with this function, such as "give me all the wells that have at least two of RHOB, DTC or DTS".
- Added the recently added `index` argument (to preserve depth units) to `Project`.
- The LAS header items EKB and EGL are now captured as `ekb` and `egl` in the `w.location` object. KB and GL are captured as `kb` and `gl`.
- Thank you Miguel de la Varga for an update that allows a trajectory to have fewer than 3 points.
- Thank you DC Slagel for an update that ensures all well header fields are populated with valid types.


## 0.4.7, 6 June 2020
- Load your well in feet! The number one most hated 'feature' has been 'fixed'... you can now pass the `index` argument to `Well.from_las()` or `Well.from_lasio()` to control how the index is interpreted. Use `'existing'` or `'original'` to keep whatever is specified in the LAS file (probably what you want).  To convert to metres, use `'m'`; to convert to feet use `'ft'`.
- In the next point release, v0.5, we will change the default behaviour to `'original'`, so if you want to keep forcing to metres, you'll have to change your code to `Well.from_las(fname, index='m')`. There is a `FutureWarning` about this.
- The `Curve` object now has a `basis_units` attribute carrying this information. Either `'m'` or `'ft'`.
- See `tutorial/Well_depth_units_v0.4.7.ipynb`.
- Thank you to Kent Inverarity for implementing this long-hoped-for feature.


## 0.4.6, 7 May 2020
- Big fix in `Location`.

## 0.4.5, 14 November 2019
- Allowed adding the NULL value when writing an LAS file with `w.to_las()`.

## 0.4.4, 22 October 2019
- Dropped support for Python 2.7 and Python 3.4, and added support for Python 3.7 and 3.8.
- Fixed `location`, whose changes were inadvertently rolled back.

## 0.4.3, October 2019
- You can now pass an `alias` dictionary to `Well.df()`, along with the list of `keys`. You can pass `keys` and `alias` to `Project.df()` as well.
- A new function, `location.trajectory()`, generates an evenly sampled trajectory, given a sample spacing in metres.
- Added `location.plot_plan()` and `location.plot_3d()` for plotting well trajectories.
- Added a new tutorial notebook, `tutorials/Location.ipynb` to demonstrate the well path capabilities of `Well.location()`. The notebook does not cover geographic CRS's. There's still a short example in `Well.ipynb`.
- Fixed some buggy behaviour when creating 'empty' wells, and added example to top of `tutorials/Well.ipynb`.
- You can now pass a URL directly to `Well.from_las()` and it will try to read it.

## 0.4.2, April 2019
- Implemented basis updating when slicing. In general, you probably want to 'slice' (get a subcurve) using `curve.to_basis()` because you can use depth to get the section you want. But if you want to use indexing, like `curve[100:110]`, this operation now updates `curve.start` so that `curve.basis` is therefore updated.
- Breaking change: `utils.top_and_tail` now only works on single arrays, and returns a single array.

## 0.4.1, 24 November 2018
- Fixed a bug in `project.df()` that was building the DataFrame incorrectly.

## 0.4.0, 20 November 2018
- There are breaking changes in this release.
- Export the curves in the current `well.data` to Pandas DataFrame with `well.df()`. Previously, this function returned the DataFrame of the associated LAS file, which is still available in `well.las.df()`.
- Export the curves in the current Project as a Pandas DataFrame with a dual index: UWI and depth.
- Made the APIs of various functions more consistent, e.g. with `keys` always being before `basis`. This regularization will continue.
- Made the way to retrieve `keys` more consistent, using the flattened list of keys, if provided, or getting all those keys corresponding to curves, if not. Some of the well methods used to break if there were striplogs in `well.data`, but they should behave a bit better now.
- Thanks to Jesper Dramsch, the documentation should now be working again. Thanks Jesper!
- Added this `CHANGES.md` file.
- Synthetics don't work anyway and are definitely broken right now. Test is withheld for now.

## 0.3.5, 20 March 2018

## 0.3.4, 15 November 2017
