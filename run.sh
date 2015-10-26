#!/bin/bash
# Kill all previous python processes
pkill -9 python
# Start three servers. Each one serves as the proposer, acceptor, and learner
python MainScript.py -i 0 -ip 127.0.0.1 127.0.0.1 127.0.0.1 -pp 29367 29368 29369 -ap 29370 29371 29372 &
python MainScript.py -i 1 -ip 127.0.0.1 127.0.0.1 127.0.0.1 -pp 29367 29368 29369 -ap 29370 29371 29372 &
python MainScript.py -i 2 -ip 127.0.0.1 127.0.0.1 127.0.0.1 -pp 29367 29368 29369 -ap 29370 29371 29372 &
