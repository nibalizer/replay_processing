sc2 replay processing
=====================


installation
------------

This package can be installed with pip as follows:

::
    git clone https://github.com/nibalizer/replay_processing
    cd replay_processing
    pip install -U replay_processing


The use of a virtualenv is recommended.


requirements
------------

* The ggtracker fork of sc2reader (https://github.com/ggtracker/sc2reader)
* spawningtool (https://github.com/StoicLoofah/spawningtool)
* A folder named 'replays' with .SC2Replay files inside



running
--------


::
    time replayscan | tee starcraft_data.csv


run time
--------

* 5m27.043s run time on 600 replays at adb4c2b952052fbbc92565440d4bb0b30d70aeb3
* 11m48.872s run time on 1600 replays at c1532d4dc5004357928fd141ce5cc78a5bbdddc6



processing
----------


Upload this data to Watson Analytics( https://watson.analytics.ibmcloud.com/)



example analytics
-----------------


![Example Chart](watson_analytics.png)




