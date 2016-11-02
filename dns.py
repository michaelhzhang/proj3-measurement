import subprocess
from utils import *
import json
import numpy as np
import matplotlib.pyplot as plot
import time
from matplotlib.backends import backend_pdf
from collections import defaultdict

def run_dig(hostname_filename, output_filename, dns_query_server=None):
    digs = []
    for hostname in hostname_filename:
        i = 0
        while i < 5:
            hostname_dig = {}
            hostname_dig[NAME_KEY] = hostname
            hostname_dig[SUCCESS_KEY], hostname_dig[QUERIES_KEY] = \
            call_dig(hostname, dns_query_server)
            digs.append(hostname_dig)
            i += 1
    # write json outputs
    with open(output_filename,'w') as out:
        json.dump(digs, out)

def call_dig(hostname, dns_query_server):
    command = construct_dig_command(hostname, dns_query_server)
    try:
        shell_output = subprocess.check_output(command, shell=True)
    except subprocess.CalledProcessError as e: # in case exit code nonzero
        shell_output = e.output
    return parse_dig_output(shell_output)

def parse_dig_output(shell_output):
    shell_output = shell_output.decode('UTF-8')
    if ((shell_output.find("A") != -1) or (shell_output.find("CNAME") != -1)):
        success = True
    else:
        success = False

    raw_queries = shell_output.split("\n\n")
    Queries = []

    for query in raw_queries:
        if (len(query) == 0 or query[0] == "="):
            continue
        query_dict = {}
        query_dict[TIME_KEY] = query[-5:-3]
        query_dict[ANSWERS_KEY] = compute_answers(query)
        Queries.append(query_dict)
    return success, Queries

def compute_answers(query):
    answers = []
    lines = query.split('\n')
    for line in lines:
        properties = line.split()
        if (len(line) == 0 or line[0] == ";"):
            continue
        answers_dict = {}
        answers_dict[QUERIED_NAME_KEY] = properties[0]
        answers_dict[ANSWER_DATA_KEY] = properties[4]
        answers_dict[TYPE_KEY] = properties[3]
        answers_dict[TTL_KEY] = properties[1]
        answers.append(answers_dict)
    return answers

def construct_dig_command(hostname, dns_query_server):
    command = "dig "
    if dns_query_server:
        command += hostname
        command += " @"
        command += dns_query_server
    else:
        command += "+trace +tries=1 +nofail "
        command += hostname
    return command

def get_average_ttls(filename):
    json_data = open(filename,"r").read()
    data = json.loads(json_data)
    root_ttl = defaultdict(list)
    tld_ttl = defaultdict(list)
    other_ttl = defaultdict(list)
    terminating_ttl = defaultdict(list)
    average_root_ttl = []
    average_tld_ttl = []
    average_other_ttl = []
    average_terminating_ttl = []

    for dig in data:
        queries = dig[QUERIES_KEY]
        for query in queries:
            answers = query[ANSWERS_KEY]
            for answer in answers:
                queried_name = answer[QUERIED_NAME_KEY]
                ttl = int(answer[TTL_KEY])
                if queried_name == ".":
                    root_ttl[dig[NAME_KEY]] += [ttl]
                elif queried_name == "com.":
                    tld_ttl[dig[NAME_KEY]] += [ttl]
                else:
                    other_ttl[dig[NAME_KEY]] += [ttl]

                if answer[TYPE_KEY] == "A" or answer[TYPE_KEY] == "CNAME":
                    terminating_ttl[dig[NAME_KEY]] += [ttl]

    for hostname in root_ttl:
        average_root_ttl += [np.mean(root_ttl[hostname])]
    for hostname in tld_ttl:
        average_tld_ttl += [np.mean(tld_ttl[hostname])]
    for hostname in other_ttl:
        average_other_ttl += [np.mean(other_ttl[hostname])]
    for hostname in terminating_ttl:
        average_terminating_ttl += [np.mean(terminating_ttl[hostname])]


    average_root_ttl = np.mean(average_root_ttl)
    average_tld_ttl = np.mean(average_tld_ttl)
    average_other_ttl = np.mean(average_other_ttl)
    average_terminating_ttl = np.mean(average_terminating_ttl)

    return [average_root_ttl, average_tld_ttl, average_other_ttl, \
    average_terminating_ttl]

def get_average_times(filename):
    json_data = open(filename,"r").read()
    data = json.loads(json_data)
    avg0, avg1 = get_query_average_times(data)
    for host in avg0:
        avg0 += [np.mean(avg0[host])]
        avg1 += [np.mean(avg1[host])]
    avg0 = np.mean(avg0)
    avg1 = np.mean(avg1)
    return [avg0, avg1]

def get_query_average_times(data):
    avgs = [defaultdict(list), defaultdict(list)]
    for dig in data:
        queries = dig[QUERIES_KEY]
        total = 0
        i = 0
        for query in queries:
            total += int(query[TIME_KEY])
            if i == 3:
                final = int(query[TIME_KEY])
            i+=1

        avgs[0][dig[NAME_KEY]] += [total]
        avgs[1][dig[NAME_KEY]] += [final]

    return [avgs[0], avgs[1]]

def generate_time_cdfs(json_filename, output_filename):
    json_data = open(json_filename,"r").read()
    data = json.loads(json_data)
    avgs = get_query_average_times(data)
    x1 = []
    x2 = []
    for key in avgs[0]:
        x1 += avgs[0][key]
        x2 += avgs[1][key]
    x1 = np.sort(x1)
    x2 = np.sort(x2)
    y1 = cdf_y_vals(x1)
    y2 = cdf_y_vals(x2)
    fig = plot.figure()
    plot.step(x1,y1)
    plot.step(x2,y2)
    plot.grid()
    plot.xlabel('ms')
    plot.ylabel('Cumulative fraction')
    plot.show()
    with backend_pdf.PdfPages(output_filename) as pdf:
        pdf.savefig(fig)

def cdf_y_vals(sorted_x_vals):
    y_vals = np.arange(len(sorted_x_vals))/float(len(sorted_x_vals))
    return y_vals

def count_different_dns_responses(filename1, filename2):
    json_data1 = open(filename1,"r").read()
    data1 = json.loads(json_data1)
    json_data2 = open(filename2,"r").read()
    data2 = json.loads(json_data2)

    dns_response1 = get_dns_response(data1,1)
    dns_response2 = get_dns_response(data2,2)
    diff1 = 0
    diff2 = 0

    for key in dns_response1:
        set1 = set(dns_response1[key])
        set2 = set(dns_response2[key])
        if len(set1) > 1:
            print key, 1
            diff1 += 1
            diff2 += 1
        elif set1 != set2:
            diff2 += 1
            print "203.160.180.2", key, 1
    return diff1, diff2

def get_dns_response(data, i):
    dns_response = {}
    for dig in data:
        queries = dig[QUERIES_KEY]
        for query in queries:
            answers = query[ANSWERS_KEY]
            for answer in answers:
                ans_type = answer[TYPE_KEY]
                if  ans_type == "A" or ans_type == "CNAME":
                    if dig[NAME_KEY] in dns_response:
                        dns_response[dig[NAME_KEY]] += [answer[ANSWER_DATA_KEY]]
                    else:
                        dns_response[dig[NAME_KEY]] = [answer[ANSWER_DATA_KEY]]
    return dns_response

def main():
    # alexa_hosts = open('alexa_top_100','r').read().split('\n')[:-1]
    # run_dig(alexa_hosts, "results/dns_output_other_server.json", "203.160.180.2")
    # run_dig(alexa_hosts, "results/dns_output_1.json")
    # SECONDS_IN_HOUR = 60*60 + 5
    # time.sleep(SECONDS_IN_HOUR)
    # run_dig(alexa_hosts, "results/dns_output_2.json")
    # get_average_ttls("results/dns_output_1.json")
    print "difference in dns response with server from makati "\
    + str(count_different_dns_responses("results/dns_output_1.json",\
    "results/dns_output_other_server.json"))
    print "difference in dns response with server from makati "\
    + str(count_different_dns_responses("results/dns_output_1.json",\
    "results/dns_output_2.json"))
    generate_time_cdfs("results/dns_output_1.json", "results/plots.pdf")

if __name__ == "__main__":
    main()
