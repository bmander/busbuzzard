Busbuzzard
==========

Inference of probabilistic schedules from empirical data about transit vehicles.

## Massage GPS data into a set of observed stop_time events

#### Step 0: Get the data

* A CSV of points logged from the NextBus API.
  * For example: https://dl.dropboxusercontent.com/u/1158424/route_5.csv.zip
  * Try to find someone with a larger data dump, to get a larger data dump.
* An unzipped GTFS that describes the service recorded in the NextBus CSV
  * Try http://www.gtfs-data-exchange.com/ for current and past GTFS feeds

#### Step 1: Slice a route out of the NextBus CSV dump

`$ python slice_route.py data/nextbus.csv data/route_27.csv 27`

#### Step 2: Chain NextBus vehicle fixes into strings representing trip instances

`$ python chain.py data/route_27.csv data/route_27_chained.csv`

#### Step 3: Assign NextBus fix chains to GTFS trips

`$ python python match.py data/route_27_chained.csv data/your_gtfs_dir 27 data/route_27_your_gtfs.matches`

#### Step 4: Cache GTFS patterns

`$ python find_gtfs_patterns.py data/your_gtfs_dir data/your_gtfs_patterns.json`

#### Step 5: Compute passbys

`$ python passby.py data/your_gtfs_dir data/your_gtfs_patterns.json data/route_27_chained.csv data/route_27_your_gtfs.matches data/route_27_your_gtfs_passbys.csv`

## Visualize scheduled and observed stop_time events

Run viz_stop.py without stop, pattern, or service_id qualifiers

`python viz_stop.py data/route_5_fallwinter_passbys.csv data/sfmta_fallwinter_2012 data/sfmta_fallwinter_2012_patterns.json`

Which complains that it needs a stop_id, but helpfully gives you some options, like:

>Pick a stop. Here are some options:<br>
>stop:3923	 count:1386<br>
>stop:3927	 count:18021<br>
>stop:4228	 count:21447<br>
>stop:4229	 count:23270<br>
>stop:4224	 count:20978<br>
>stop:4225	 count:23290<br>

Pick one and run again with a stop

`python viz_stop.py data/route_5_fallwinter_passbys.csv data/sfmta_fallwinter_2012 data/sfmta_fallwinter_2012_patterns.json 4228`

Now it complains that you need a pattern, but supplies some, like:

>Pick a pattern. Here are some options:<br>
>pattern:271	 count:1068<br>
>pattern:169	 count:18722<br>
>pattern:213	 count:1657<br>

Pick one and run again, then it compains that you need a service_id, on account of how a pattern can run on different service_ids

`python viz_stop.py data/route_5_fallwinter_passbys.csv data/sfmta_fallwinter_2012 data/sfmta_fallwinter_2012_patterns.json 4228 169`

>Pick a service_id. Here are some options:<br>
>service_id:1	 count:13714<br>
>service_id:3	 count:2544<br>
>service_id:2	 count:2464<br>

Finally select a service_id:

`python viz_stop.py data/route_5_fallwinter_passbys.csv data/sfmta_fallwinter_2012 data/sfmta_fallwinter_2012_patterns.json 4228 169 1`

Which brings up a pyplot window illustrating a timeline of every scheduled and observed event at stop 4228, on pattern 169, with a service_id of 1.

![alt tag](https://raw.github.com/bmander/busbuzzard/master/static/observed_schedule.png)
