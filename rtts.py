import subprocess
import numpy as np
import json
import matplotlib.pyplot as plot
from matplotlib.backends import backend_pdf

def run_ping(hostnames, num_packets, raw_ping_output_filename,
             aggregated_ping_output_filename):
    rtts_by_host = {}
    rtt_summaries_by_host = {}
    for hostname in hostnames:
        rtts = call_ping(hostname, num_packets)
        rtts_by_host[hostname] = rtts
        summary_stats = compute_summary_stats(rtts)
        rtt_summaries_by_host[hostname] = summary_stats
    # write json outputs
    with open(raw_ping_output_filename,'w') as out:
        json.dump(rtts_by_host, out)
    with open(aggregated_ping_output_filename,'w') as out:
        json.dump(rtt_summaries_by_host, out)

def call_ping(hostname, num_packets):
    command = construct_ping_command(hostname, num_packets)
    try:
        shell_output = subprocess.check_output(command, shell=True)
    except subprocess.CalledProcessError as e: # in case exit code nonzero
        shell_output = e.output
    rtts = parse_ping_output(shell_output, num_packets)
    return rtts

def construct_ping_command(hostname, num_packets):
    command = "ping -c "
    command += str(num_packets + 1) # Ping one more than needed
    command += " "
    command += hostname
    return command

def parse_ping_output(shell_output, num_packets):
    lines = shell_output.split('\n')
    rtts = []
    for line in lines:
        if (len(rtts) == num_packets): # might call ping more times
            break
        if ((len(line) > 0) and
            (not is_first_line(line)) and
            (not is_statistics_line(line))):
            rtt = parse_ping_line(line)
            rtts.append(rtt)
    return rtts

def is_first_line(line):
    return ((len(line) >= 4) and (line[:4] == 'PING'))

def is_statistics_line(line):
    return ((len(line) >= 3) and (line[:3] == "---"))

def is_timeout(line):
    phrase = "Request timeout for icmp_seq"
    return ((len(line) >= len(phrase)) and (line[:len(phrase)] == phrase))

def parse_ping_line(line):
    if is_timeout(line):
        return -1.0
    tokens = line.split()
    time_token = tokens[-2]
    assert(time_token[:5] == "time=")
    rtt = float(time_token[5:])
    return rtt

def compute_summary_stats(rtt_list):
    assert(len(rtt_list) > 0)
    num_drops = 0
    num_pings = len(rtt_list)
    for rtt in rtt_list:
        if rtt == -1.0:
            num_drops += 1
    if (num_drops == num_pings):
        drop_rate = 100.0
        max_rtt = -1.0
        median_rtt = -1.0
    else:
        drop_rate = num_drops / float(num_pings)
        drop_rate *= 100
        no_drops = np.array(rtt_list)
        no_drops = no_drops[no_drops != -1.0]
        max_rtt = max(no_drops)
        median_rtt = np.median(no_drops)
    result_dict = {}
    result_dict["drop_rate"] = drop_rate
    result_dict["max_rtt"] = max_rtt
    result_dict["median_rtt"] = median_rtt
    return result_dict

def plot_median_rtt_cdf(agg_ping_results_filename, output_cdf_filename):
    json_data = open(agg_ping_results_filename,"r").read()
    data = json.loads(json_data)
    medians = []
    for hostname in data:
        median = data[hostname]['median_rtt']
        if median != -1.0:
            medians.append(median)
    x = np.sort(medians)
    y = cdf_y_vals(x)
    fig = plot.figure()
    plot.step(x,y)
    plot.grid()
    plot.xlabel('ms')
    plot.ylabel('Cumulative fraction')
    plot.show()
    with backend_pdf.PdfPages(output_cdf_filename) as pdf:
        pdf.savefig(fig)

def cdf_y_vals(sorted_x_vals):
    y_vals = np.arange(len(sorted_x_vals))/float(len(sorted_x_vals))
    return y_vals

def plot_ping_cdf(raw_ping_results_filename, output_cdf_filename):
    json_data = open(raw_ping_results_filename,"r").read()
    data = json.loads(json_data)
    fig = plot.figure()
    for hostname in data:
        rtts = data[hostname]
        no_drops = np.array(rtts)
        no_drops = no_drops[no_drops != -1.0]
        assert(len(no_drops) > 0)
        x = np.sort(no_drops)
        y = cdf_y_vals(x)
        plot.plot(x,y,label=hostname)
    plot.grid()
    plot.xlabel('ms')
    plot.ylabel('Cumulative fraction')
    plot.legend()
    plot.show()
    with backend_pdf.PdfPages(output_cdf_filename) as pdf:
        pdf.savefig(fig)

def main():
    # rtt_a
    print("Alexa")
    alexa_hosts = open('alexa_top_100','r').read().split('\n')[:-1]
    run_ping(alexa_hosts, 10, 'results/rtt_a_raw.json','results/rtt_a_agg.json')

    # rtt_b
    print('part b')
    b_hosts = ['google.com', 'todayhumor.co.kr', 'zanvarsity.ac.tz', 'taobao.com']
    run_ping(b_hosts, 500, 'results/rtt_b_raw.json', 'results/rtt_b_agg.json')

    # Plotting
    print("plotting a")
    plot_median_rtt_cdf('results/rtt_a_agg.json','plots/rtt_a_median_cdf.pdf')

    print('plotting b')
    plot_ping_cdf('results/rtt_b_raw.json','plots/rtt_b_raw_cdf.pdf')

if __name__ == "__main__":
    main()

