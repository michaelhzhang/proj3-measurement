import rtts

print("plotting a")
rtts.plot_median_rtt_cdf('results/rtt_a_agg.json','plots/rtt_a_median_cdf.pdf')

print('plotting b')
rtts.plot_ping_cdf('results/rtt_b_raw.json','plots/rtt_b_raw_cdf.pdf')
