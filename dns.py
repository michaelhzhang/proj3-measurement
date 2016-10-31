import subprocess
from utils import *
import json
import os
import numpy as np

def run_dig(hostname_filename, output_filename, dns_query_server=None):
    digs = []
    for hostname in hostname_filename:
        i = 0
        while i < 5:
            hostname_dig = {}
            hostname_dig[NAME_KEY] = hostname
            hostname_dig[SUCCESS_KEY], hostname_dig[QUERIES_KEY] = call_dig(hostname, dns_query_server)
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
    total_root_ttl = []
    total_tld_ttl = []
    total_other_ttl = []
    total_terminating_ttl = []

    for dig in data:
        answers = dig[QUERIES_KEY][ANSWERS_KEY]
        root = [answers[key][TTL_KEY] for key in answers if \
            answers[key][QUERIED_NAME_KEY] == "."]
        tld = [answers[key][TTL_KEY] for key in answers if \
            answers[key][QUERIED_NAME_KEY] == "com."]
        other = [answers[key][TTL_KEY] for key in answers if \
            answers[key][QUERIED_NAME_KEY] != "." and
            answers[key][QUERIED_NAME_KEY] != "com."]
        term = [answers[key][TTL_KEY] for key in answers if \
            answers[key][TYPE_KEY] == "A" and
            answers[key][TYPE_KEY] == "CNAME"]
        total_root_ttl += np.mean(root)
        total_tld_ttl += np.mean(tld)
        total_other_ttl += np.mean(other)
        total_terminating_ttl += np.mean(term)

    average_root_ttl = np.mean(total_root_ttl)
    average_tld_ttl = np.mean(total_tld_ttl)
    average_other_ttl = np.mean(total_other_ttl)
    average_terminating_ttl = np.mean(total_terminating_ttl)

    return [average_root_ttl, average_tld_ttl, average_other_ttl, \
        average_terminating_ttl]


def get_average_times(filename):
    json_data = open(filename,"r").read()
    data = json.loads(json_data)
    avgs = [[],[]]
    for dig in data:

        queries = dig[QUERIES_KEY]
        total = 0
        for query in queries:
            total += query[TIME_KEY]
            if query[TYPE_KEY] == "A" or query[TYPE_KEY] == "CNAME":
                final = query[TIME_KEY]

def generate_time_cdfs(json_filename, output_filename):
    pass

def count_different_dns_responses(filename1, filename2):
    pass

def main():
    alexa_hosts = open('alexa_top_100','r').read().split('\n')[:-1]
    run_dig(alexa_hosts, "results/dns_output_1.json")
    # SECONDS_IN_HOUR = 60*60
    # time.sleep(SECONDS_IN_HOUR)
    # run_dig(alexa_hosts, "results/dns_output_2.json")

if __name__ == "__main__":
    main()
