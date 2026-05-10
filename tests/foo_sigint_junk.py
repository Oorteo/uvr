#!/usr/bin/env uvr

# Example script for testing Ctrl+C (SIGINT) handling in uvr
# Run this script via uvr to check if junk output is suppressed on interruption.
import time

print("Starting infinite loop. Press Ctrl+C to interrupt.")
try:
    while True:
        print("Working... (press Ctrl+C)")
        time.sleep(1)
except KeyboardInterrupt:
    print("Caught KeyboardInterrupt (SIGINT) cleanly, with no traceback noise.")
