import json

def count_routes(filename):
    lines = open(filename,"r").read().strip().split('\n')
    routes = {}
    for line in lines:
        print("NEW RUN")
        print("---------------------------------------")
        data = json.loads(line)
        for host in data:
            if host == "timestamp":
                continue
            print("---------------------------------------")
            print("HOST: " + host)
            print("---------------------------------------")
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
                print("CHECKING NEW ROUTE")
                print("###################")
                if (routes_equal(route, curr_route)):
                    new = False
            if new:
                routes[host].append(curr_route)
    print(routes["www.berkeley.edu"])
    counts = {}
    for host in routes:
        counts[host] = len(routes[host])
    print(counts)

def routes_equal(route1,route2):
    if len(route1) != len(route2):
        return False
    for i in range(len(route1)):
        print("HOP: " + str(i))
        print("PREVIOUS")
        print(route1[i])
        print("CURRENT")
        print(route2[i])
        if route1[i] != route2[i]:
            print("NOT EQUAL")
            return False
    print("ROUTES EQUAL")
    return True

if __name__ == "__main__":
    count_routes("results/tr_a.json")
