#!/usr/bin/env python3

"""
View `journalctl --dmesg` (including past boots) and collect data to analyze for CPU core stability. In addition, take previous curve optimizer settings (as well as when they were active) and make a recommendation for the most aggressive settings where no errors are occurring.

Tracks events that are known to be associated with unstable hardware, including:
- segfaults connected with a specific core (containing "Core ##, Socket ##").
"""
import subprocess
import json
import re
import argparse
from typing import Dict#, List

class CONFIG:
    """Global configuration."""
    MAX_BOOTS: int = -1 # -1 = all, otherwise the max number of boots to analyze
    SCAN: bool = False # Scan journalctl entries and create a log file
    ADD_CURVE: bool = False # Add a curve optimizer setting
    LOGS_FILENAME: str = "dmesg_logs.json"
    BOOTS: str = "all" # default all, but optionally specify a boot or maybe range of boots or the "--since=" syntax from journalctl

class Arguments:
    """ Manage command line arguments """
    def __init__(self):
        self.create_arguments()

    def create_arguments(self):
        """
        Creates an ArgumentParser with our arguments in it.
        Sets up the variables for the rest of the run
        """
        parser = argparse.ArgumentParser(description="Analyze dmesg logs for instances of errors that are likely to be associated with CPU core instability, then assemble a record of them in json. In addition, create a record of curve optimizer curve optimizer settings (per core) with a timestamp of when they became active so the errors can be compared to the configuration at the time of the error. This can then be used to build the \"maximum safe\" curve optimizer settings, where no (or only an acceptable number) of errors occur on that core.")
        scan = parser.add_argument_group("Scan Logs")
        curves = parser.add_argument_group("Curve Optimizer")
        scan.add_argument("-s", "--scan", action="store_true", help=f"Scan dmesg logs (maybe others in the future) for errors associated with CPU instability and record them in {CONFIG.LOGS_FILENAME}.")
        curves.add_argument("-c", "--curves", action="store_true", help="Enter curve optimizer settings and a timestamp for when they were active.")

class DmesgReader:
    """ Read dmesg history and convert it to a usable format """
    def __init__(self):
        self.boots = self.list_boots()
        self.logs = self.create_dmesg_history()

    def create_dmesg_history(self) -> list[Dict]:
        """ Returns a dict of dmesg history, for all boots"""
        # TODO: Make this collect data only for specified time frames.
        entries = []
        for boot in self.boots:
            boot_logs = self.read_dmesg_logs(boot)
            if len(boot_logs) > 0:
                entries.extend(boot_logs)
        return entries


    def list_boots(self) -> list[int]:
        """ List all boots journalctl has logs for """
        boots = []
        boot_list = subprocess.run(["journalctl", "--list-boots"], stdout=subprocess.PIPE, text=True, check=False)
        lines = boot_list.stdout.split("\n")
        for line in lines:
            if line: # If it's not a blank line
                # Match optional whitespace, a `-` if present, and any number of digits.
                # Ex: "-10", " -3", "0", or "   -150"
                num_boot = re.match(r"(\s*-*\d+)", line)
                if num_boot:
                    boots.append(int(num_boot.group(1)))
        return boots

    def read_dmesg_logs(self, boot: int) -> list[Dict]:
        """ Call `journalctl --dmesg` for specified boot and return all log lines for it. """
        logs = []
        result = subprocess.run(["journalctl", "--dmesg", "-b", str(boot)], stdout=subprocess.PIPE, text=True, check=False)

        lines = result.stdout.split("\n")
        for line in lines:
            if line: # If it's not a blank line
                log_entry = self.parse_log_line(line, boot)
                if log_entry:
                    logs.append(log_entry)
        return logs


    def parse_log_line(self, line: str, boot: int) -> Dict[str, str]:
        """
        Check if the line is one of the ones we're looking for. Sample line:
            May 29 18:37:47 fedora kernel: gldriverquery[271469]: segfault at fffffffffffff000 ip 00007fd4dc38cf00 sp 00007fff8a16d590 error 5 in libLLVM.so.18.1[7fd4dc00c000+3afb000] likely on CPU 15 (core 15, socket 0)
        If this is what we're looking for, cut it up into parts and then return a dict of the parts.
        """
        message = line.split(":", 1)[1]
        time_match = re.match(r"(\w+ \d+ \d{2}:\d{2}:\d{2}) (.+)", line)
        core_match = re.search(r"\(core (\d+), socket (\d+)\)", line)
        if core_match and time_match:
            core_number = int(core_match.group(1))
            socket_number = int(core_match.group(2))
            timestamp, remainder = time_match.groups()
            source = remainder.split(":", 1)[0]
            if core_number >= 0:
                return {"timestamp": timestamp, "boot": boot, "source": source, "message": message, "core": core_number, "socket": socket_number}
        return None

    def to_json(self) -> str:
        """ Convert logs into json """
        return json.dumps(self.logs, indent=3)

    def save_to_file(self, filename: str):
        """ Write the collected logs to disk """
        with open(filename, "w", encoding="UTF-8") as f:
            json.dump(self.logs, f, indent=3)

if __name__ == "__main__":
    dmesg_logs = DmesgReader()
    #print(dmesg_logs.to_json())
    dmesg_logs.save_to_file(CONFIG.LOGS_FILENAME)
