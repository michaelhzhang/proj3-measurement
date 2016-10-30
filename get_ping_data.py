import rtts

# rtt_a
print("Alexa")
alexa_hosts = open('alexa_top_100','r').read().split('\n')
rtts.run_ping(alexa_hosts, 10, 'results/rtt_a_raw.json','results/rtt_a_agg.json')

# rtt_b
print('part b')
b_hosts = ['google.com', 'todayhumor.co.kr', 'zanvarsity.ac.tz', 'taobao.com']
rtts.run_ping(b_hosts, 500, 'results/rtt_b_raw.json', 'results/rtt_b_agg.json')

