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


arguments
---------
--replay_folder (-R): Path to directory we want to pull replay data from

--max_replays (-M): Maximum number of replay files to parse (should be int)

--worker_threads (-T): Number of threads used to parse files (defaults to 5)

--all_matches (-a) [NOT IMPLEMENTED YET]: if set, parses all replays not just 1v1 matchups

--verbose (-v): Print all output if set




running
--------

### If you want to time this function:

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
