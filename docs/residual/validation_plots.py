import matplotlib.pyplot as plt
import numpy as np
from obspy.core import UTCDateTime

from geomagio.residual.Calculation import calculate
from geomagio.residual import WebAbsolutesFactory

observatory = "BOU"
starttime = UTCDateTime("2020-01-01")
endtime = UTCDateTime("2020-07-01")

readings = WebAbsolutesFactory().get_readings(
    observatory=observatory,
    starttime=starttime,
    endtime=endtime,
    include_measurements=True,
)

# define orignal absolute and baseline arrays for each type
H_o_abs = [reading.absolutes[1].absolute for reading in readings]
H_o_baseline = [reading.absolutes[1].baseline for reading in readings]
D_o_abs = [reading.absolutes[0].absolute for reading in readings]
D_o_baseline = [reading.absolutes[0].baseline for reading in readings]
Z_o_abs = [reading.absolutes[2].absolute for reading in readings]
Z_o_baseline = [reading.absolutes[2].baseline for reading in readings]

# define calculated absolute and baseline arrays for each type
H_c_abs = []
H_c_baseline = []
D_c_abs = []
D_c_baseline = []
Z_c_abs = []
Z_c_baseline = []
# loop through 6 months of readings
for reading in readings:
    # skip calculation when not enough information exists within reading
    try:
        reading = calculate(reading)
    except TypeError:
        D_c_abs.append(np.nan)
        D_c_baseline.append(np.nan)

        H_c_abs.append(np.nan)
        H_c_baseline.append(np.nan)

        Z_c_abs.append(np.nan)
        Z_c_baseline.append(np.nan)
        continue
    # append calculated values from null method calculations
    D_c_abs.append(reading.absolutes[0].absolute)
    D_c_baseline.append(reading.absolutes[0].baseline)

    H_c_abs.append(reading.absolutes[1].absolute)
    H_c_baseline.append(reading.absolutes[1].baseline)

    Z_c_abs.append(reading.absolutes[2].absolute)
    Z_c_baseline.append(reading.absolutes[2].baseline)

t = np.arange(1, len(readings) + 1)

plt.figure(figsize=(15, 14))

plt.subplot(6, 1, 1)
plt.plot(t, H_o_abs, "b.", label="Null")
plt.plot(t, H_c_abs, "r.", label="Residual")
plt.legend()
plt.ylabel("nT", fontsize=15)
plt.title("H Absolute(2020-01-01 - 2020-07-01)", fontsize=20)

plt.subplot(6, 1, 2)
plt.plot(t, D_o_abs, "b.", label="Null")
plt.plot(t, D_c_abs, "r.", label="Residual")
plt.legend()
plt.ylabel("deg", fontsize=15)
plt.title("D Absolute(2020-01-01 - 2020-07-01)", fontsize=20)

plt.subplot(6, 1, 3)
plt.plot(t, Z_o_abs, "b.", label="Null")
plt.plot(t, Z_c_abs, "r.", label="Residual")
plt.legend()
plt.ylabel("nT", fontsize=15)
plt.title("Z Absolute(2020-01-01 - 2020-07-01)", fontsize=20)

plt.subplot(6, 1, 4)
plt.plot(t, H_o_baseline, "b.", label="Null")
plt.plot(t, H_c_baseline, "r.", label="Residual")
plt.legend()
plt.ylabel("nT", fontsize=15)
plt.title("H Baseline(2020-01-01 - 2020-07-01)", fontsize=20)

plt.subplot(6, 1, 5)
plt.plot(t, D_o_baseline, "b.", label="Null")
plt.plot(t, D_c_baseline, "r.", label="Residual")
plt.legend()
plt.ylabel("deg", fontsize=15)
plt.title("D Baseline(2020-01-01 - 2020-07-01)", fontsize=20)

plt.subplot(6, 1, 6)
plt.plot(t, Z_o_baseline, "b.", label="Null")
plt.plot(t, Z_c_baseline, "r.", label="Residual")
plt.legend()
plt.ylabel("nT", fontsize=15)
plt.xlabel("reading #", fontsize=15)
plt.title("Z Baseline(2020-01-01 - 2020-07-01)", fontsize=20)

plt.tight_layout()
plt.show()
