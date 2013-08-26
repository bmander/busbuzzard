"""Match Nextbus dirtag to GTFS pattern"""

from urllib2 import urlopen
from xml.dom.minidom import parseString
import simplejson as json
from difflib import SequenceMatcher

THRESHOLD_RATIO = 0.8

def get_nextbus_dirtags(agency,routetag):
	fp = urlopen( "http://webservices.nextbus.com/service/publicXMLFeed?command=routeConfig&a=%s&r=%s"%(agency,routetag) )
	doc = parseString( fp.read() )

	for node in doc.getElementsByTagName("direction"):
		tag = node.getAttribute("tag")
		title = node.getAttribute("title")
		name = node.getAttribute("name")

		stop_tags = [x.getAttribute("tag") for x in node.getElementsByTagName("stop")]

		yield {'tag':tag,'title':title,'name':name,'stop_tags':stop_tags}

def main(agency, routetag, patterns_filename):
	print "getting dirtags for agency:%s routetag:%s"%(agency,routetag)
	dirtags = list( get_nextbus_dirtags( agency, routetag ) )
	print "done"

	patterns, trips = json.loads( open(patterns_filename).read() )

	print "%d dirtags"%len(dirtags)
	print "%d patterns"%len(patterns)

	for dirtag in dirtags:
		sm = SequenceMatcher()
		sm.set_seq1( dirtag["stop_tags"] )

		pattern_found = False
		for pattern_id, pattern in patterns.items():
			sm.set_seq2( pattern )
			ratio = sm.ratio()
			if ratio > THRESHOLD_RATIO:
				print dirtag["tag"], pattern_id, ratio
				pattern_found = True

		if not pattern_found:
			print dirtag["tag"], None, None

if __name__=='__main__':
	import sys
	if len(sys.argv)<4:
		print "usage: python cmd.py agency routetag patterns_filename"
		exit()

	agency = sys.argv[1]
	routetag = sys.argv[2]
	patterns_filename = sys.argv[3]

	main(agency,routetag,patterns_filename)