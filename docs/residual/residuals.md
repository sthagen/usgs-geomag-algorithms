# Tools:


## Spreadsheet Absolutes Factory:
Tool for gathering a single reading from a formatted spreadsheet or several readings from a directory of spreadsheets. Outputs include measurements and absolutes. Format examples can be found at https://code.usgs.gov/ghsc/geomag/geomag-algorithms/-/tree/master/etc/residual.

### Usage:
```python
from geomagio.residual import SpreadsheetAbsolutesFactory

saf = SpreadsheetAbsolutesFactory()

reading = saf.parse_spreadsheet(path="../../etc/residual/DED-20140952332.xlsm")
```

## Web Absolutes Factory:
Tool for gathering several readings from webservice queries. Output can optionally include measurements, but will always return absolutes as long as they are available.

### Usage:
```python
from geomagio.residual import WebAbsolutesFactory
from obspy.core import UTCDateTime

waf = WebAbsolutesFactory()

starttime = UTCDateTime("2020-01-01")
endtime = UTCDateTime("2020-10-01")

readings = waf.get_readings(observatory="BOU", starttime=starttime, endtime=endtime, include_measurements=True)
```

## Calculation:
Implements residual method for a reading to derive new absolute values. See https://gi.copernicus.org/articles/6/419/2017/gi-6-419-2017.pdf for theoretical information.

### Usage:
```python
from geomagio.residual.Calculation import calculate
# assumes that a reading is gathered from either of the package's factories
output_reading = calculate(reading)
```

NOTE: Input readings require measurements. Current measurements are made using the null method and will not include residual values. The residual method is backwards compatible with the null method, but resulting absolute values will not be identical. Residuals utilize small angle approximations, which account for small changes in output values.

# Validation:
Backwards compatibility allows for legacy null measurements to have their absolute values recalculated by the residual method. The following figure serves to display the change in values when recalculated with the residual method. Data is gathered from the Boulder magnetic observatory and includes readings from a six month time span.(01/2020 - 07/2020)

![Residual Validation Plot](../images/residual_null_validation.png)

