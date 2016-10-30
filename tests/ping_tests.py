import sys
sys.path.insert(0,'..')
import rtts

# Compare against example
print("Compare against example: ")
sample_ping = '../examples/sample_ping.txt'
ping_string = ""
for line in open(sample_ping,'r'):
    ping_string += line
rtt_list = rtts.parse_ping_output(ping_string, 10)
summ_stats = rtts.compute_summary_stats(rtt_list)
print("rtts:")
print(rtt_list)
print("summary:")
print(summ_stats)

print("Testing dropped packets:")
rtts.run_ping(['amazon.com'],2,'amazon_ping_test_raw.json','amazon_ping_test_agg.json')

# integration test
# rtts.run_ping(['google.com'],10,"google_ping_test_raw.json","google_ping_test_agg.json")

