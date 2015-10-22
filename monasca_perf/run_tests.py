import subprocess
import sys
import argparse
import datetime

# Available tests
# Disk.sh to check initial and final disk
# Disk_io.sh to check disk_io runs every thirty seconds
# Kafka_topics.sh checks the lags from kafka every thirty seconds
# Top.sh grabs the top output continuously throughout the tests
# Query_alarms
# Metrics per a second
# Alarm transistions
# VSQL Alarm transistions


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query_api", help="Run script to emulate load on our API. Queries alarm-list from api",
                        action="store_true", required=False)
    parser.add_argument("--query_alarm_state", help="Query current alarms by state", action="store_true", required=False)
    parser.add_argument("--query_metrics_per_second", help="Query metrics per second", action="store_true",
                        required=False)
    parser.add_argument("--query_alarm_transitions", help="Query alarm transitions per a minute", action="store_true",
                        required=False)
    parser.add_argument("--output_directory",
                        help="Output directory to place result files. Defaults to current directory", default='',
                        required=False)
    parser.add_argument("--vertica_password",
                        help="Vertica password for disk.sh and alarm_transitions.sh", default='password',
                        required=False)
    return parser.parse_args()


def main():

    start_time = datetime.datetime.utcnow().isoformat()

    args = parse_args()

    with open(args.output_directory + 'initial_disk', "w") as stdout:
        subprocess.Popen("./disk.sh " + args.vertica_password, shell=True, stdout=stdout)

    kafka_process = subprocess.Popen("exec ./kafka_topics.sh " + args.output_directory + 'kafka_info', shell=True)
    disk_process = subprocess.Popen("exec ./disk_writes.sh " + args.output_directory + 'disk_io', shell=True)
    top_process = subprocess.Popen("exec ./top.sh " + args.output_directory + 'system_info', shell=True)

    if args.query_alarm_transitions:
        alarm_transitions_process = subprocess.Popen("exec ./alarm_transitions.sh " + args.output_directory +
                                                     'alarm_transitions ' + args.vertica_password, shell=True)

    if args.query_api:
        subprocess.Popen("python query_alarms.py", shell=True)
    if args.query_alarm_state:
        subprocess.Popen("python query_alarm_state.py --output_directory " + args.output_directory, shell=True)

    try:
        kafka_process.wait()
    except KeyboardInterrupt:
        with open(args.output_directory + 'final_disk', "w") as stdout:
            subprocess.Popen("./disk.sh " + args.vertica_password, shell=True, stdout=stdout)
        kafka_process.kill()
        disk_process.kill()
        top_process.kill()
        if args.query_alarm_transitions:
            alarm_transitions_process.kill()
        if args.query_metrics_per_second:
            subprocess.call("python query_metrics_per_second.py " + start_time + " --output_directory " +
                            args.output_directory, shell=True)

if __name__ == "__main__":
    sys.exit(main())

