import subprocess
import json
import time

def run_traceroute(hostnames, num_packets, output_filename):
    curr_time = time.time()
    with open(output_filename,"w") as out:
        out.write("TIMESTAMP: " + str(curr_time) + "\n")
        for hostname in hostnames:
            out.write("ORIG_HOSTNAME: " + hostname + "\n")
            trace_command = construct_command(hostname, num_packets)
            trace_output = subprocess.check_output(trace_command, shell=True)
            out.write(trace_output + "\n")

def construct_command(hostname, num_packets):
    command = "traceroute -a -q "
    command += str(num_packets)
    command += " "
    command += hostname
    command += " 2>&1" # Redirect stderr to stdout
    return command

def parse_traceroute(raw_traceroute_filename, output_filename):
    pass

