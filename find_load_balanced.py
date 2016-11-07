import json

def count_num_ips(filename):
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

if __name__ == "__main__":
    count_num_ips("results/tr_a.json")

