#!/usr/bin/env python

import sys
import socket
import getopt
import logging


PORT = 81
TOHOST = "127.0.0.1"
TOPORT = 80
DIR = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

############################################################################
#
#   This is main()
#
############################################################################

def main():
    global PORT, TOHOST, TOPORT, DIR

    try:
        opts, args = getopt.getopt(sys.argv[1:], "", ["debug", "verbose", "port=", "toport=", "tohost=", "dir="])
    except getopt.GetoptError as err:
        print(str(err))
        sys.exit(2)

    for opt, arg in opts:
        if opt == "--debug":
            logging.basicConfig(level=logging.DEBUG)
        elif opt == "--verbose":
            logging.basicConfig(level=logging.INFO)
        elif opt == "--port":
            PORT = int(arg)
        elif opt == "--toport":
            TOPORT = int(arg)
        elif opt == "--tohost":
            TOHOST = arg
        elif opt == "--dir":
            DIR = arg

    ah = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ah.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ah.bind(("0.0.0.0", PORT))
    ah.listen(10)

    logger.info("Entering main loop.")
    while True:
        try:
            ch, addr = ah.accept()
            logger.info("Accepting client from {}, port {}.".format(*addr))

            pid = os.fork()
            if pid == 0:
                # This is the child
                ah.close()
                Run(ch)
                sys.exit(0)
            else:
                # This is the parent
                ch.close()
        except Exception as err:
            logger.exception("An error occurred: {}".format(err))

def Run(ch):
    th = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        th.connect((TOHOST, TOPORT))
    except socket.error as err:
        logger.error("Child: Failed to connect tunnel to {}, port {}.".format(TOHOST, TOPORT))
        return

    logger.info("Child: Connecting tunnel to {}, port {}.".format(TOHOST, TOPORT))

    if DIR:
        with open("{}/tunnel{}.log".format(DIR, os.getpid()), "w") as fh:
            ch.setblocking(1)
            th.setblocking(1)

            while True:
                try:
                    cbuffer = ch.recv(4096)
                    if not cbuffer:
                        break
                    fh.write(cbuffer)
                    th.sendall(cbuffer)
                except socket.error as err:
                    logger.error("Child: Error while reading from client: {}".format(err))
                    break
    else:
        ch.setblocking(1)
        th.setblocking(1)

        while True:
            try:
                cbuffer = ch.recv(4096)
                if not cbuffer:
                    break
                th.sendall(cbuffer)
            except socket.error as err:
                logger.error("Child: Error while reading from client: {}".format(err))
                break

    ch.close()
    th.close()

if __name__ == "__main__":
    main()
