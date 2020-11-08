#
# constants
#
# Copyright (c) 2020 Daniel Dean <dd@danieldean.uk>.
#
# Licensed under The MIT License a copy of which you should have
# received. If not, see:
#
# http://opensource.org/licenses/MIT
#

# Sleep interval between checking and logging in seconds.
SLEEP_INTERVAL = 900

# Socket numbers for devices (Energenie module only supports 4).
HEAT_MAT_SOCKET = 1
PUMP_SOCKET = 2
FAN_SOCKET = 3
LIGHT_SOCKET = 4

# Temperature thresholds (used for heat mat and fan).
LOW_TEMPERATURE = 15
HIGH_TEMPERATURE = 25

# Humidity thresholds (used for pump, could be mister, etc).
LOW_HUMIDITY = 60
