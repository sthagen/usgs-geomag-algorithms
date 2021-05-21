# Metadata Webservice Model Parameters
* **id**: Database id. Separates records

* **metadata_id**: Database foreign key. Separates different versions of the same record

* **created_by**: Creator name

* **created_time**: Time record was created

* **updated_by**: Editor/reviewer name

* **updated_time**: Time record was edited or reviewed at

* **starttime/endtime**: Meaning depends on metadata category(see starttime/endtime usage section)

* **network**: Defaults to NT(geomagnetism edge network)

* **station**: 3-Letter station ID

* **channel**: 3-Letter edge channel

* **location**: 2-Letter edge location code

* **category**: 1 of 5 metadata categories(see category section)

* **priority**: Integer identifying importance of record. High priority records receive a higher number

* **data_valid**: Indicator of valid information outside of the metadata dictionary

* **metadata_valid**: Indicator of valid information within the metadata dictionary

* **metadata**: Dictionary holding specific information to each metadata category

* **comment**: Comment section for creator or non-reviewer

* **review_comment**: Comment section for reviewer

* **status**: 1 of 3 record statuses(see status section)

# starttime/endtime Usage
* **observatory/instrument/adjusted-matrix**: Start and end times indicate time ranges where a record holds applicable information to an observatory(epoch)
  * a new adjusted matrix has a starttime of its creation time
  * a separate(newer) adjusted matrix has a starttime of its creation time. The previous matrix's endtime is set to this matrix's starttime
* **reading/flag**: Start and end times indicate time ranges that are applicable to only the metadata record
  * a flag that indicates the starttime and entime of a disturbance
  * a reading that indicates the starttime and endtime of measurements taken by an observer
# Categories
* **reading**: field measurements and residual method calculations

    https://code.usgs.gov/ghsc/geomag/geomag-algorithms/-/blob/master/geomagio/residual/Reading.py

* **adjusted-matrix**: adjusted matrices and performance metrics for use by the adjusted algorithm

    https://code.usgs.gov/ghsc/geomag/geomag-algorithms/-/blob/master/geomagio/adjusted/AdjustedMatrix.py

* **flag**: indicators of observatory outages or data issues(spikes, gaps, offsets, etc.)

* **observatory**: Information related to an observatory(agency name, station id, sensor orientation, etc.)

    https://code.usgs.gov/ghsc/geomag/geomag-algorithms/-/blob/master/geomagio/api/ws/Observatory.py

* **instrument**: holds information(serial numbers, volt/bin constants, etc.) pertaining to theodolites or magnetometers

    https://code.usgs.gov/ghsc/geomag/geomag-algorithms/-/blob/master/geomagio/Metadata.py

# Status
* **new**: when a new record is created
* **updated**: when a new record is edited by its creator or an approved user
* **reviewed**: after a record is reviewed by an approved user
* **deleted**: archive a record that is invalid or incomplete

