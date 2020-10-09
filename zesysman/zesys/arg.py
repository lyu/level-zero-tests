#!/usr/bin/env python3
# Copyright (C) 2020 Intel Corporation
# SPDX-License-Identifier: MIT

import argparse
import os.path

from . import logger
from . import otree
from . import output
from . import state
from . import util
from . import zes_wrap

#
# Parse arguments
#
def parse():
    #
    # Option parser
    #
    helpFormatter=lambda prog: argparse.HelpFormatter(prog, max_help_position=48)
    parser = argparse.ArgumentParser(description="Access SYSMAN services", formatter_class=helpFormatter)

    parser.add_argument("-v","--version", action='version', version="%(prog)s " + state.ZESYSMAN_PROG_VERSION,
                        help="report version information")
    parser.add_argument("--driver", metavar='DRV', nargs='+', help="specify driver (index/UUID)")
    parser.add_argument("-d", "--device", metavar='D', nargs='+', help="specify device (index/UUID)")
    parser.add_argument("-i", "--show-inventory", action='store_true', help="show inventory data")
    parser.add_argument("-l", "--show-telemetry", action='store_true', help="show telemetry data")
    parser.add_argument("-t", "--show-temp", action='store_true', help="show temperature")
    parser.add_argument("-p", "--show-power", action='store_true', help="show power")
    parser.add_argument("-c", "--show-freq", "--show-clocks", action='store_true', help="show frequency")
    parser.add_argument("-u", "--show-util", action='store_true', help="show utilization")
    parser.add_argument("-m", "--show-mem", action='store_true', help="show memory stats")
    parser.add_argument("-x", "--show-pci", action='store_true', help="show PCI bandwidth")
    parser.add_argument("--show-fabric-ports", action='store_true', help="show fabric ports")
    parser.add_argument("-b", "--show-standby", action='store_true', help="show standby promotion")
    parser.add_argument("-e", "--show-errors", action='store_true', help="show errors")
    parser.add_argument("-a", "--show-all", action='store_true', help="show all sysman attributes")
    parser.add_argument("--show-device", action='store_true', help="show device attributes")
    parser.add_argument("--show-processes", action='store_true', help="show process usage")
    parser.add_argument("--show-scheduler", action='store_true', help="show scheduler mode")
    parser.add_argument("--show-diag", action='store_true', help="show diagnostic test suites")
    parser.add_argument("--show-topo", choices=["matrix","graph","info"], help="show topology map")
    parser.add_argument("--verbose", action='store_true', help="show extra attributes")
    parser.add_argument("--poll", metavar='TIME', type=int,
                        help="set sampling interval (in s by default)")
    parser.add_argument("--iterations", metavar='NUM', type=int,
                        help="samples to collect (0 = until stopped)")
    parser.add_argument("--enable-critical-temp", nargs=1, metavar='IDX', type=int,
                        help="enable critical temperature sensor")
    parser.add_argument("--disable-critical-temp", nargs=1, metavar='IDX', type=int,
                        help="disable critical temperature sensor")
    parser.add_argument("--enable-t1-low-to-high", nargs=1, metavar='IDX', type=int,
                        help="enable low-to-high temperature threshold 1")
    parser.add_argument("--disable-t1-low-to-high", nargs=1, metavar='IDX', type=int,
                        help="disable low-to-high temperature threshold 1")
    parser.add_argument("--enable-t1-high-to-low", nargs=1, metavar='IDX', type=int,
                        help="enable high-to-low temperature threshold 1")
    parser.add_argument("--disable-t1-high-to-low", nargs=1, metavar='IDX', type=int,
                        help="disable high-to-low temperature threshold 1")
    parser.add_argument("--set-t1-threshold", nargs=2, metavar=('IDX','C'), type=int,
                        help="set temperature threshold 1")
    parser.add_argument("--enable-t2-low-to-high", nargs=1, metavar='IDX', type=int,
                        help="enable low-to-high temperature threshold 2")
    parser.add_argument("--disable-t2-low-to-high", nargs=1, metavar='IDX', type=int,
                        help="disable low-to-high temperature threshold 2")
    parser.add_argument("--enable-t2-high-to-low", nargs=1, metavar='IDX', type=int,
                        help="enable high-to-low temperature threshold 2")
    parser.add_argument("--disable-t2-high-to-low", nargs=1, metavar='IDX', type=int,
                        help="disable high-to-low temperature threshold 2")
    parser.add_argument("--set-t2-threshold", nargs=2, metavar=('IDX','C'), type=int,
                        help="set temperature threshold 2")
    parser.add_argument("--set-power", nargs='+', metavar=('POW','TAU'),
                        help="set sustained power limit")
    parser.add_argument("--set-burst-power", nargs='+', metavar=('POW',''),
                        help="set burst power limit")
    parser.add_argument("--set-peak-power", nargs='+', metavar=('POW',''),
                        help="set peak power limit")
    parser.add_argument("--set-energy-threshold", nargs='+', metavar=('J',''),
                        help="set energy threshold")
    parser.add_argument("--set-freq", nargs='+', metavar=('MIN','MAX'), help="set frequency limits")
    parser.add_argument("--set-scheduler", nargs='+', metavar=('IDX','MODE'), help="set scheduler mode")
    parser.add_argument("--clear-errors", action='store_true', help="clear error counters")
    parser.add_argument("--set-error-thresholds", nargs='+', type=int, metavar=('TYPE','N'),
                        help="set error thresholds")
    parser.add_argument("--enable-fabric-ports", nargs='*', type=int, metavar='IDX',
                        help="enable fabric ports")
    parser.add_argument("--disable-fabric-ports", nargs='*', type=int, metavar='IDX',
                        help="disable fabric ports")
    parser.add_argument("--enable-beaconing", nargs='*', type=int, metavar='IDX',
                        help="enable port beaconing")
    parser.add_argument("--disable-beaconing", nargs='*', type=int, metavar='IDX',
                        help="disable port beaconing")
    parser.add_argument("--set-standby", metavar='MODE', help="set sleep state promotion mode")
    parser.add_argument("--reset", action='store_true', help="reset specified device")
    parser.add_argument("--force", action='store_true', help="forcibly kill processes on reset")
    parser.add_argument("-y", "--yes", action='store_true', help="do not ask for reset confirmation")
    parser.add_argument("--run-diag", nargs='+', metavar=('SUITE','N'),
                        help="run diagnostic test suites")
    parser.add_argument("-f", "--format", metavar='FMT', choices=["list","xml","table","csv"],
                        help="specify output format (list/xml/table/csv)")
    parser.add_argument("--output", metavar='FILE', help="output to FILE")
    parser.add_argument("--tee", action='store_true', help="print to standard output also")
    parser.add_argument("--indent", metavar='COUNT', type=int,
                        help="use COUNT space (or -COUNT tab) indents")
    parser.add_argument("--style", choices=["condensed","aligned"], help="change output style")
    parser.add_argument("--uuid-index", action='store_true', help="use UUID as index")
    parser.add_argument("--ascii", action='store_true', help="use only 7-bit ascii characters")

    #
    # Developer-only options
    #
    if util.developer_mode():
        dparse = parser
    else:
        dparse = argparse.ArgumentParser()

    dparse.add_argument("-n", "--dry-run", action='store_true', help="do not make any state changes")
    # dparse.add_argument("--save-profile", metavar='PROF', help="save device configuration")
    # dparse.add_argument("--restore-profile", metavar='PROF', help="restore device configuration")
    # dparse.add_argument("--subdevice", action='store_true', help="report by subdevice")
    dparse.add_argument("--tiny-uuid", action='store_true', help="print tiny device UUIDs")
    dparse.add_argument("--debug", action='store_true', help="debug (for development only)")
    dparse.add_argument("--reset-freq", action='store_true', help="reset frequency limits")
    dparse.add_argument("--hide-timestamp", action='store_true',
                        help="hide timestamps when iterating")
    dparse.add_argument("--wait-events", nargs='*', metavar=('MSEC','MASK'), help="wait for events")
    dparse.add_argument("--show-fans", action='store_true', help="show fans")
    dparse.add_argument("--set-fan-speed-default", nargs=1, type=int, metavar='IDX',
                        help="set fan to default speed")
    dparse.add_argument("--set-fan-speed-rpm", nargs=2, type=int, metavar=('IDX','RPM'),
                        help="set fan to fixed speed in RPM")
    dparse.add_argument("--set-fan-speed-percent", nargs=2, type=int, metavar=('IDX','%'),
                        help="set fan to fixed speed in percent of max")
    dparse.add_argument("--set-fan-speed-table-rpm", nargs='+', type=int, metavar=('IDX','N'),
                        help="set fan to temperature table in RPM")
    dparse.add_argument("--set-fan-speed-table-percent", nargs='+', type=int, metavar=('IDX','N'),
                        help="set fan to temperature table in percent of max")
    dparse.add_argument("--show-firmware", action='store_true', help="show firmware")
    dparse.add_argument("--flash-firmware", nargs=1, metavar='FILE', help="flash firmware from FILE")
    dparse.add_argument("--set-oc-freq", nargs=2, metavar=('IDX','FRQ'),
                        help="Set overclock frequency target")
    dparse.add_argument("--set-oc-volts", nargs=3, metavar=('IDX','V','V'),
                        help="Set overclock voltage/offset targets")
    dparse.add_argument("--set-oc-off", nargs=1, type=int, metavar='IDX',
                        help="Set overclock mode to OFF")
    dparse.add_argument("--set-oc-override", nargs=1, type=int, metavar='IDX',
                        help="Set overclock mode to OVERRIDE")
    dparse.add_argument("--set-oc-interpolate", nargs=1, type=int, metavar='IDX',
                        help="Set overclock mode to INTERPOLATING")
    dparse.add_argument("--set-oc-fixed", nargs=1, type=int, metavar='IDX',
                        help="Set overclock mode to FIXED")
    dparse.add_argument("--set-oc-max-current", nargs=2, metavar=('IDX','A'),
                        help="Set max overclock current")
    dparse.add_argument("--set-oc-max-temp", nargs=2, metavar=('IDX','C'),
                        help="Set max overclock temperature")
    dparse.add_argument("--show-oc", action='store_true', help="show overclocking")
    dparse.add_argument("--show-leds", action='store_true', help="show leds")
    dparse.add_argument("--enable-led", nargs=1, type=int, metavar='IDX', help="enable LED")
    dparse.add_argument("--disable-led", nargs=1, type=int, metavar='IDX', help="disable LED")
    dparse.add_argument("--set-led-color", nargs='+', metavar=('IDX','COLOR'), help="set LED color")
    dparse.add_argument("--ansi-256", action='store_true', help="use ANSI-256 colors")
    dparse.add_argument("--show-perf", action='store_true', help="show performance factors")
    dparse.add_argument("--set-perf", nargs=2, metavar=('IDX','VAL'), help="set performance factor")
    dparse.add_argument("--show-psu", action='store_true', help="show power supplies")

    #
    # Get option values/defaults
    #
    args = parser.parse_args()

    if not util.developer_mode():
        darg = dparse.parse_args([])
        for a,v in darg.__dict__.items():
            args.__dict__[a] = v

    otree.setNodeClassByName(args.format)

    if args.poll is not None and args.iterations is not None:
        args.iterations = 0

    if args.iterations is not None:
        if args.iterations < 1:
            state.maxIterations = sys.maxint
        else:
            state.maxIterations = args.iterations

        args.show_telemetry = True

    if args.output and args.output != "-":
        if args.format is None:
            setotree.NodeClassByExtension(os.path.splitext(args.output)[1].lower())
        try:
            fil = open(args.output, "w")
        except:
            logger.pr.fail("Could not open file", args.output, "for writing")
        else:
            logger.pr.outputFile = fil
            logger.pr.teeOutput = args.tee

    if args.indent is not None:
        if args.indent >= 0:
            state.indentStr = " " * args.indent
        else:
            state.indentStr = "\t" * -args.indent

    if args.tiny_uuid:
        output.deviceUUID = tinyUUID

    if args.debug:
        logger.pr.debugFile = sys.stderr

    state.condensedList = (args.style == "condensed")

    if args.uuid_index:
        state.indexAttribute = "UUID"

    if args.ansi_256:
        state.addAnsi256ColorBlock = True

    state.hideTimestamp = args.hide_timestamp

    return args

def parseMilliwatts(opts):
    value = 0.0
    multiplier = 1000.0
    remainder = []
    if opts:
        opt = opts.pop(0).lower()
        split = None
        if "m" in opt:
            split = opt.index("m")
        if "w" in opt:
            if split is None:
                split = opt.index("w")
            else:
                split = min(split, opt.index("w"))
        if split is None:
            rest = opts
        else:
            opt, rest = opt[:split], [opt[split:]] + opts

        try:
            value = float(opt)
        except:
            hitRemainder = True
            if opt not in ["d", "def", "default"]:
                logger.pr.err("WARNING: Illegal power value (" + opt + "), using default/0")
        else:
            hitRemainder = False

        for opt in rest:
            opt = opt.lower()
            if hitRemainder:
                remainder.append(opt)
            else:
                hitRemainder = True
                if opt in ["m", "mw", "mwatt", "mwatts", "milliwatt", "milliwatts"]:
                    multiplier = 1.0
                elif opt not in ["w", "wt", "watt", "watts"]:
                    remainder.append(opt)
    else:
        logger.pr.err("WARNING: No power value specified, using default/0")

    return int(value * multiplier), remainder

def parseMilliseconds(opts):
    value = 0.0
    multiplier = 1000.0
    remainder = []
    if opts:
        opt = opts.pop(0).lower()
        split = None
        if "m" in opt:
            split = opt.index("m")
        if "s" in opt:
            if split is None:
                split = opt.index("s")
            else:
                split = min(split, opt.index("s"))
        if split is None:
            rest = opts
        else:
            opt, rest = opt[:split], [opt[split:]] + opts

        try:
            value = float(opt)
        except:
            hitRemainder = True
            if opt not in ["d", "def", "default"]:
                logger.pr.err("WARNING: Illegal time value (" + opt + "), using default/0")
        else:
            hitRemainder = False

        for opt in rest:
            opt = opt.lower()
            if hitRemainder:
                remainder.append(opt)
            else:
                hitRemainder = True
                if opt in ["m", "ms", "msec", "msecond", "mseconds", "millisecond", "milliseconds"]:
                    multiplier = 1.0
                elif opt not in ["s", "sec", "second", "seconds"]:
                    remainder.append(opt)
    else:
        logger.pr.err("WARNING: No time value specified, using default/0")

    return int(value * multiplier), remainder

def parseJoules(opts):
    value = 0.0
    multiplier = 1.0
    remainder = []
    if opts:
        opt = opts.pop(0).lower()
        split = None
        if "m" in opt:
            split = opt.index("m")
        if "k" in opt:
            if split is None:
                split = opt.index("k")
            else:
                split = min(split, opt.index("k"))
        if "j" in opt:
            if split is None:
                split = opt.index("j")
            else:
                split = min(split, opt.index("j"))
        if split is None:
            rest = opts
        else:
            opt, rest = opt[:split], [opt[split:]] + opts

        try:
            value = float(opt)
        except:
            hitRemainder = True
            logger.pr.err("WARNING: Illegal energy value (" + opt + "), using 0.0 J")
        else:
            hitRemainder = False

        for opt in rest:
            opt = opt.lower()
            if hitRemainder:
                remainder.append(opt)
            else:
                hitRemainder = True
                if opt in ["m", "mj", "mjoule", "mjoules", "millijoule", "millijoules"]:
                    multiplier = 0.001
                elif opt in ["k", "kj", "kjoule", "kjoules", "kilojoule", "kilojoules"]:
                    multiplier = 1000.0
                elif opt in ["j", "joule", "joules"]:
                    remainder.append(opt)
    else:
        logger.pr.err("WARNING: No energy value specified, using 0.0 J")

    return value * multiplier, remainder

def parseMHz(opts):
    value = 0.0
    multiplier = 1.0
    remainder = []
    if opts:
        opt = opts.pop(0).lower()
        split = None
        if "m" in opt:
            split = opt.index("m")
        if "g" in opt:
            if split is None:
                split = opt.index("g")
            else:
                split = min(split, opt.index("g"))
        if "h" in opt:
            if split is None:
                split = opt.index("h")
            else:
                split = min(split, opt.index("h"))
        if "k" in opt:
            if split is None:
                split = opt.index("k")
            else:
                split = min(split, opt.index("k"))
        if split is None:
            rest = opts
        else:
            opt, rest = opt[:split], [opt[split:]] + opts

        try:
            value = float(opt)
        except:
            hitRemainder = True
            if opt not in ["d", "def", "default"]:
                logger.pr.err("WARNING: Illegal power value (" + opt + "), using default/0")
        else:
            hitRemainder = False

        for opt in rest:
            opt = opt.lower()
            if hitRemainder:
                remainder.append(opt)
            else:
                hitRemainder = True
                if opt in ["g", "ghz", "gigahertz"]:
                    multiplier = 1000.0
                elif opt in ["k", "khz", "kilohertz"]:
                    multiplier = 1e-3
                elif opt in ["h", "hz", "hertz"]:
                    multiplier = 1e-6
                elif opt not in ["m", "mhz", "megahertz"]:
                    remainder.append(opt)
    else:
        logger.pr.err("WARNING: No power value specified, using default/0")

    return value * multiplier, remainder

def parseSchedulerMode(opts):
    opt, remainder = opts[0].lower(), opts[1:]

    if opt in ["timeout", "time", "to", "t", "zes_sched_mode_timeout"]:
        mode = zes_wrap.ZES_SCHED_MODE_TIMEOUT
    elif opt in ["timeslice", "slice", "ts", "s", "zes_sched_mode_timeslice"]:
        mode = zes_wrap.ZES_SCHED_MODE_TIMESLICE
    elif opt in ["exclusive", "exc", "ex", "e", "x", "zes_sched_mode_exclusive"]:
        mode = zes_wrap.ZES_SCHED_MODE_EXCLUSIVE
    elif opt in ["cudebug", "debug", "dbg", "db", "d", "g", "zes_sched_mode_compute_unit_debug"]:
        mode = zes_wrap.ZES_SCHED_MODE_COMPUTE_UNIT_DEBUG
    else:
        logger.pr.err("ERROR: Unrecognized scheduler mode", opt)
        raise ValueError(opt)

    return mode, remainder

def parseMicroseconds(opts):
    value = 0.0
    multiplier = 1000000.0
    remainder = []
    if opts:
        opt = opts.pop(0).lower()
        split = None
        if "u" in opt:
            split = opt.index("u")
        if "m" in opt:
            split = opt.index("m")
        if "s" in opt:
            if split is None:
                split = opt.index("s")
            else:
                split = min(split, opt.index("s"))
        if split is None:
            rest = opts
        else:
            opt, rest = opt[:split], [opt[split:]] + opts

        hitRemainder = True

        if opt in ["n", "none"]:
            value = zes_wrap.ZES_SCHED_WATCHDOG_DISABLE
            multiplier = 1
        elif opt not in ["d", "def", "default"]:
            try:
                value = float(opt)
                hitRemainder = False
            except:
                logger.pr.err("WARNING: Illegal time value (" + opt + "), using default")

        for opt in rest:
            opt = opt.lower()
            if hitRemainder:
                remainder.append(opt)
            else:
                hitRemainder = True
                if opt in ["u", "us", "usec", "usecond", "useconds", "microsecond", "microseconds"]:
                    multiplier = 1.0
                elif opt in ["m", "ms", "msec", "msecond", "mseconds", "millisecond", "milliseconds"]:
                    multiplier = 1000.0
                elif opt not in ["s", "sec", "second", "seconds"]:
                    remainder.append(opt)

    return int(value * multiplier), remainder