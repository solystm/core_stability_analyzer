#!/usr/bin/env python3

import subprocess
import json
import re
from typing import List, Dict

class DmesgReader:
    def __init__(self):
        self.logs = []
    
    def read_dmesg_logs(self):
        
        str_journalctl = f"journalctl --dmesg"
        result = subprocess.run(["journalctl", "--dmesg", "-b", "-1"], stdout=subprocess.PIPE, text=True)

        lines = result.stdout.split("\n")
        for line in lines:
            if line:
                log_entry = self.parse_log_line(line)
                self.logs.append(log_entry)


    def parse_log_line(self, line: str) -> Dict[str, str]:
        message = line.split(":", 1)[1]
        time_match = re.match(r"(\w+ \d+ \d{2}:\d{2}:\d{2}) (.+)", line)
        core_match = re.search(r"\(core (\d+), socket (\d+)\)", line)
        print(core_match)
        if core_match:
            core_number = int(core_match.group(1))
            socket_number = int(core_match.group(2))
            if time_match:
                timestamp, remainder = time_match.groups()
                source = remainder.split(":", 1)[0]
                # message = remainder.split(":", 1)[1]
                # host, source, message = remainder_with_host.partition(":")
                # source, message  = remainder.partition(":")
                return {"timestamp": timestamp, "source": source, "message": message, "core": core_number, "socket": socket_number}
            else:
                return {"timestamp": "Unknown", "source": "Unknown", "message": message}
        else:
            core_number = -1
            socket_number = -1
            return {"timestamp": "Unknown", "source": "Unknown", "message": message, "core": core_number, "socket": socket_number}

    def to_json(self) -> str:
        return json.dumps(self.logs, indent=3)

    def save_to_file(self, filename: str):
        with open(filename, "w") as f:
            json.dump(self.logs, f, indent=3)

if __name__ == "__main__":
    dmesg_logs = DmesgReader()
    dmesg_logs.read_dmesg_logs()
    #print(dmesg_logs.to_json())
    dmesg_logs.save_to_file("dmesg_logs.json")
