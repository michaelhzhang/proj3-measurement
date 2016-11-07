import json

def count_ASes(filename):
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

if __name__ == "__main__":
    count_ASes("results/tr_a.json")
