import subprocess
import json
import time
import re

TIMESTAMP_PHRASE = "TIMESTAMP: "
HOSTNAME_PHRASE = "ORIG_HOSTNAME: "
TRACEROUTE_OUTPUT_PHRASE = "traceroute"
REVERSE_PHRASE = "REVERSE"

def run_traceroute(hostnames, num_packets, output_filename):
    curr_time = time.time()
    with open(output_filename,"w") as out:
        to_write = TIMESTAMP_PHRASE + str(curr_time) + "\n"
        for hostname in hostnames:
            to_write += HOSTNAME_PHRASE + hostname + "\n"
            trace_command = construct_command(hostname, num_packets)
            trace_output = subprocess.check_output(trace_command, shell=True)
            to_write += trace_output
        to_write = to_write.strip() # Strip trailing whitespace
        out.write(to_write)

def construct_command(hostname, num_packets):
    command = "traceroute -a -q "
    command += str(num_packets)
    command += " "
    command += hostname
    command += " 2>&1" # Redirect stderr to stdout
    return command

def parse_traceroute(raw_traceroute_filename, output_filename):
    trace_output = open(raw_traceroute_filename,"r").read().strip().split('\n')
    if is_reverse(trace_output): # For route symmetry, output formats different
        result = parse_reverse_traceroute(trace_output)
    else:
        result = parse_normal_traceroute(trace_output)
    with open(output_filename,"a") as out: # Append instead of overwrite
        json.dump(result, out)
        out.write("\n") # Add newline

def is_reverse(trace_output):
    return ((len(trace_output)>0) and (trace_output[0] == REVERSE_PHRASE))

def parse_normal_traceroute(trace_output):
    curr_hostname = None
    result = {}
    curr_trace = None
    curr_hop = None
    count = 0
    for line in trace_output:
        if is_timestamp(line):
            result["timestamp"] = parse_timestamp(line)
        elif is_hostname(line):
            if curr_hostname is not None: # new trace
                curr_trace.append(curr_hop)
                record_results(curr_hostname, curr_trace, result)
                curr_hop = None
            curr_hostname = parse_hostname(line)
            curr_trace = []
        elif is_traceroute_output(line):
            continue # skip
        elif is_new_hop(line):
            if curr_hop is not None:
                curr_trace.append(curr_hop)
            curr_hop = []
            curr_hop.append(parse_hop(line))
        elif is_continuing_hop(line):
            curr_hop.append(parse_hop(line))
        else:
            print("Unexpected line: ")
            print(line)
    # Finish parsing last hop and trace
    if curr_hop is not None:
        curr_trace.append(curr_hop)
    record_results(curr_hostname, curr_trace, result)
    return result

def is_timestamp(line):
    length = len(TIMESTAMP_PHRASE)
    return ((len(line)>=length) and (line[:length] == TIMESTAMP_PHRASE))

def parse_timestamp(line):
    tokens = line.split()
    timestamp = tokens[1]
    return timestamp

def is_hostname(line):
    length = len(HOSTNAME_PHRASE)
    return ((len(line)>=length) and (line[:length] == HOSTNAME_PHRASE))

def record_results(curr_hostname, curr_trace, result):
    result[curr_hostname] = curr_trace

def parse_hostname(line):
    tokens = line.split()
    hostname = tokens[1]
    return hostname

def is_traceroute_output(line):
    length = len(TRACEROUTE_OUTPUT_PHRASE)
    return ((len(line)>=length) and (line[:length] == TRACEROUTE_OUTPUT_PHRASE))

def is_new_hop(line):
    tokens = line.split()
    return ((len(tokens) > 0) and is_int(tokens[0]))

def is_int(string):
    try:
        int(string)
        return True
    except ValueError:
        return False

def is_continuing_hop(line):
    tokens = line.split()
    return ((len(tokens) > 0) and is_AS(tokens[0]))

def is_AS(token):
    """Checks if token is an ASN"""
    p = re.compile('\[\w*\]') # \w* means 0 or more alphanumerics
    return (p.match(token) is not None)

def parse_hop(line):
    if is_new_hop(line):
        AS_index = 1 # Is the ASN the 0th or 1st token?
    else:
        AS_index = 0
    tokens = line.split()
    assert(len(tokens)>=3)
    ASN = tokens[AS_index].lstrip('[AS').rstrip(']')
    name = tokens[AS_index+1]
    ip = tokens[AS_index+2].lstrip('(').rstrip(')')
    result = {}
    if ASN == "*": # Not responding
        result["ASN"] = "None"
        result["name"] = "None"
        result["ip"] = "None"
    else:
        result["ASN"] = ASN
        result["name"] = name
        result["ip"] = ip
    return result

def parse_reverse_traceroute(trace_output): # TODO
    curr_hostname = None
    result = {}
    curr_trace = None
    curr_hop = None
    count = 0
    for line in trace_output:
        if is_timestamp(line):
            result["timestamp"] = parse_timestamp(line)
        elif is_hostname(line):
            if curr_hostname is not None: # new trace
                curr_trace.append(curr_hop)
                record_results(curr_hostname, curr_trace, result)
                curr_hop = None
            curr_hostname = parse_hostname(line)
            curr_trace = []
        elif is_new_hop(line):
            if curr_hop is not None:
                curr_trace.append(curr_hop)
            curr_hop = []
            curr_hop.append(parse_reverse_hop(line))
        elif is_continuing_reverse_hop(line):
            curr_hop.append(parse_reverse_hop(line))
        else: continue # ignore all other outputs
    # Finish parsing last hop and trace
    if curr_hop is not None:
        curr_trace.append(curr_hop)
    record_results(curr_hostname, curr_trace, result)
    return result

def is_continuing_reverse_hop(line):
    tokens = line.split()
    return ((len(tokens) >= 3) and is_AS(tokens[3]))

def parse_reverse_hop(line):
    if is_new_hop(line):
        name_index = 1 # Is the name the 0th or 1st token?
    else:
        name_index = 0
    tokens = line.split()
    assert(len(tokens)>=3)
    name = tokens[name_index]
    ip = re.search('(\(\d+\.\d+\.\d+\.\d+\))',line) # IP numbers of form (###.###.###.###)
    ASN = re.search('(\[AS\s\d+\])',line) # AS numbers of form [AS ####]
    result = {}
    if name == "*": # Not responding
        result["ASN"] = "None"
        result["name"] = "None"
        result["ip"] = "None"
    else:
        if ASN is None:
            result["ASN"] = "None"
        else:
            result["ASN"] = ASN.group(1).lstrip('[AS ').rstrip(']')
        result["name"] = name
        if ip is None:
            result["ip"] = "None"
        else:
            result["ip"] = ip.group(1).lstrip('(').rstrip(')')
    return result

def part_a_run(run_num):
    print("Running part a at time " + time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()))
    part_a_sites = ["google.com",
                    "facebook.com",
                    "www.berkeley.edu",
                    "allspice.lcs.mit.edu",
                    "todayhumor.co.kr",
                    "www.city.kobe.lg.jp",
                    "www.vutbr.cz",
                    "zanvarsity.ac.tz"]
    tmp_file = "tmp_traces/tr_a_tmp_" + str(run_num)
    run_traceroute(part_a_sites,5,tmp_file)
    parse_traceroute(tmp_file,"results/tr_a.json")

def part_b_run_from_our_computer():
    print("Running part b from our computer at time " + time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()))
    part_b_servers = ["tpr-route-server.saix.net",
                      "route-server.ip-plus.net",
                      "route-views.oregon-ix.net",
                      "route-views.on.bb.telus.com"]
    run_traceroute(part_b_servers,5,"tmp_traces/tr_b_tmp")
    parse_traceroute("tmp_traces/tr_b_tmp","results/tr_b.json")

def part_b_parse_reverse():
    parse_traceroute("reverse_traces/combined-reverse-traces","results/tr_b.json")

def count_ASes(filename):
    """ For short answer a.2"""
    lines = open(filename,"r").read().strip().split('\n')
    ASNs = {}
    for line in lines:
        data = json.loads(line)
        for host in data:
            if host == "timestamp":
                continue
            if host not in ASNs:
                ASNs[host] = set([])
            hops = data[host]
            for hop in hops:
                for entry in hop:
                    ASN = entry["ASN"]
                    if ASN != "None":
                        ASNs[host].add(ASN)
    ASN_counts = {}
    for host in ASNs:
        ASN_counts[host] = len(ASNs[host])
    print(ASNs)
    print(ASN_counts)

def count_unique_routes(filename):
    """ for short answer a.4"""
    lines = open(filename,"r").read().strip().split('\n')
    routes = {}
    for line in lines:
        data = json.loads(line)
        for host in data:
            if host == "timestamp":
                continue
            if host not in routes:
                routes[host] = []
            hops = data[host]
            curr_route = []
            for hop in hops:
                ips = set([])
                for entry in hop:
                    ip = entry["ip"]
                    if ip != "None":
                        ips.add(ip)
                curr_route.append(ips)
            new = True
            for route in routes[host]:
                if (routes_equal(route, curr_route)):
                    new = False
            if new:
                routes[host].append(curr_route)
    counts = {}
    for host in routes:
        counts[host] = len(routes[host])
    print(counts)

def routes_equal(route1,route2):
    if len(route1) != len(route2):
        return False
    for i in range(len(route1)):
        if route1[i] != route2[i]:
            return False
    return True

def count_ips_per_hop(filename):
    """for short answer a.3"""
    lines = open(filename,"r").read().strip().split('\n')
    ips_per_hop = {}
    for line in lines:
        data = json.loads(line)
        for host in data:
            if host == "timestamp":
                continue
            if host not in ips_per_hop:
                ips_per_hop[host] = {}
            hops = data[host]
            hop_counts = ips_per_hop[host]
            for i in range(len(hops)):
                if i not in hop_counts:
                    hop_counts[i] = set([])
                curr_hop = hops[i]
                for entry in curr_hop:
                    ip = entry["ip"]
                    if ip != "None":
                        hop_counts[i].add(ip)
    print(ips_per_hop)
    num_ips_per_hop = {}
    for host in ips_per_hop:
        counts = {}
        hops = ips_per_hop[host]
        for i in hops:
            hop_ips = hops[i]
            counts[i] = len(hop_ips)
        num_ips_per_hop[host] = counts
    print(num_ips_per_hop)

def main():
    pass
    # part_b_run_from_our_computer()

    #SECONDS_IN_HOUR = 60*60
    #num_a_runs = 5
    #for i in range(num_a_runs):
    #    part_a_run(i)
    #    if (i < (num_a_runs-1)):
    #        time.sleep(SECONDS_IN_HOUR)

if __name__ == "__main__":
    main()
