"""
*******
MQTTany
*******

:Author: Michael Murton
"""
# Copyright (c) 2019 MQTTany contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

__version__ = "0.3.7"

import signal, time, sys, argparse
import multiprocessing as mproc
from queue import Empty as QueueEmptyError

import logger, modules
log = logger.get_logger()

queue = mproc.Queue()

class GracefulKiller:
    """ handles SIGINT and SIGTERM """
    kill_now = False
    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.kill_now = True


def get_args():
    """
    Get arguments
    """
    parser = argparse.ArgumentParser(description="MQTTany allows you to connect things to MQTT")
    parser.add_argument("-v", "--verbose", action="count", help="turn on debug logging")
    parser.add_argument("config_file", nargs='?', default="/etc/mqttany.yml", metavar="CONFIG_FILE", help="path to configuration file (default '/etc/mqttany.yml')")
    parser.add_argument("-V", "--version", action="version", version="MQTTany {}".format(__version__), help="show version and exit")
    return parser.parse_args()


if __name__ == '__main__':
    args = get_args()
    if args.verbose > 0:
        logger.set_level(logger.DEBUG)

    mproc.current_process().name = "mqttany"
    killer = GracefulKiller()
    poison_pill = False

    log.info("MQTTany {version} starting".format(version=__version__))

    try:
        if not modules.load(args.config_file): exit(1)

        while not killer.kill_now:
            try: # to get an item from the queue
                message = queue.get_nowait()
            except QueueEmptyError:
                time.sleep(0.1) # 100ms
            else:
                poison_pill = True
                log.debug("Received poison pill")

    except:
        modules.unload()
        raise

    else:
        log.info("MQTTany stopping")
        modules.unload()

        if poison_pill:
            log.info("MQTTany exiting with errors")
            exit(1)
        else:
            log.info("MQTTany stopped")
            exit(0)
