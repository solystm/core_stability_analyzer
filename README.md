# Core Stability Analyzer

Reads `journalctl --dmesg` (including past boots) to collect data about events on CPU cores that could indicate CPU instability, ex from faulty hardware or overclocking. Particularly useful with AMD's Precision Boost Overdrive (PBO2) Curve Optimizer.

Looks for events in the form of `(Core ##, Socket 0)` where the ## is any one or two numbers. Might include targeting sockets other than 0, but 0 is the default. Also may include targeting specific cores to watch suspect cores.
