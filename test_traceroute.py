import traceroute
#traceroute.parse_traceroute('examples/modified_traceroute_sample.txt','test_trace')

traceroute.run_traceroute(["twitter.com","google.com"],5,'test_tmp')
traceroute.parse_traceroute('test_tmp','test_trace')
