# Metadata Webservice Model Parameters

## Metadata id:
* **id**: Database id

* **metadata_id**: Indicates old version of metadata when set

## User information:

* **created_by**: user who created record

* **created_time**: time record was created

* **updated_by**: user that last changed record(empty when new)

* **updated_time**: time of last record change

# Status:
* **status**: 1 of 4 record statuses
  * **new**: when a new record is created
  * **updated**: when a new record is edited by an approved user
  * **reviewed**: after a record is reviewed by an approved user
  * **deleted**: archive a record that is invalid or incomplete

* **metadata_valid**: Whether record is valid and should be used in processing

* **review_comment**: Comments from reviewer about why record is valid/invalid

# Details:
* **category**: 1 of 5 metadata types
  * **reading**: field measurements and residual method calculations

    https://code.usgs.gov/ghsc/geomag/geomag-algorithms/-/blob/master/geomagio/residual/Reading.py

  * **adjusted-matrix**: adjusted matrices and performance metrics for use by the adjusted algorithm

      https://code.usgs.gov/ghsc/geomag/geomag-algorithms/-/blob/master/geomagio/adjusted/AdjustedMatrix.py

  * **flag**: indicators of observatory outages or data issues(spikes, gaps, offsets, etc.)

  * **observatory**: Information related to an observatory(agency name, station id, sensor orientation, etc.)

      https://code.usgs.gov/ghsc/geomag/geomag-algorithms/-/blob/master/geomagio/api/ws/Observatory.py

  * **instrument**: holds information(serial numbers, volt/bin constants, etc.) pertaining to theodolites or magnetometers

* **comment**: Comments from users entering or editing metadata(non-review related)

* **data_valid**: Whether referenced data is valid/invalid during a given time range

* **metadata**: Information specific to each metadata category

* **priority**: If multiple records reference the same time, higher priority takes precedence

* **starttime/endtime**: time that metadata applies to(instrument/observatory/adjusted-matrix) or time metadata was collected at(flag/reading)

# Reference Data:
* **network**: Defaults to NT(geomagnetism edge network)

* **station**: Station/observatory ID

* **channel**: 3-Letter edge channel. When null, applies to entire station

* **location**: 2-Letter edge location code. When null, applies to entire station