# PaxosMadeSimpleMadeSimple
# Still not simple enough!
# Developer: Liang Luo & Ming Liu

1. Introduction
In this project, we implement a replicated state machine and use a simple Lock service to demonstrate it.

2. Design & Implementation
2-1. Assumptions

2-2. Proposer

2-3. Lock service

2-4. Acceptor
The data structure of the acceptor includes three queues: RequestNumberQueue, ConsensusQueue, and ProposalQueue. The RequestNumberQueue saves the highest accepted proposal number for each instance while the ConsensusQueue and ProposalQueue record the accepted value and promised proposal number of each instance.

The protocol of the acceptor works as follows:
(a) When it receives the PREPARE request, it firstly compares with its promised proposal number. If it's higher, the acceptor will send a promise request with a tuple <highest accepted number, accepted value>. Note that the highest accepted number is -1 in the beginning. Meanwhile, it also updates its ProposalQueue. If not, the acceptor will send a DENIAL request.
(b) When it receives the ACCEPT request, it also compared with its promised pproposal number. If it's higher or equal, the acceptor will (1) accept this value, (2) send the acceptance knowledgement to the proposer, and (3)update its RequestNumberQueue and ConsensusQueue. If not, the acceptor will send a DENIAL request.


 save the 

3. How to run the experiment

4. Trace Analysis

5. Discussions
(1) Why the acceptor maintain the queue instead of just one variable?
Because we'd like to deal with multiple instances.
(2) Why do have the denial request?
The denial request is used to indicate the proposal whether the proposal number is smaller than the acceptor's expectation.


This is a somewhat easy toy Paxos implementation.
The Paxos serves as an infraustructure for the application layer protocols.

Each node acts as Acceptor, Proposer and Learner.

We require servers to not skip ahead - i.e. if instance i of Paxos is undone, i+1th cannot start.
We do not maintain logs.
We do allow servers to catch up, i.e., servers can be added to the Paxos group anytime. We support this using a simple approach - the newly added server acts as if it was late in proposing the first rounds. By executing Paxos Basic, these servers are allowed to catch up and compete for the next instance. Note this is exactly the same mechanism that we used to synchronize consensus.
The servers are not eager, meaning they would not usually care about the consensus unless they would like to propose. We choose this property because usually the distinguished leader is alive. If not, some commands need to be flushed (i.e., we use Nops to force servers to catch up to the latest consensus instances).


[Proposer 0] Request Receive REQUEST:-1:-1:(23, 'LOCK', 'b')
[Proposer 0] Prepared Issued PREPARE:0:0:('127.0.0.1', 60598, 23, 'LOCK', 'b')
[Proposer 0] Promise Receive PROMISE:0:0:(-1, ('127.0.0.1', 60598, 23, 'LOCK', 'b'))
[Proposer 0] Promise Receive PROMISE:0:0:(-1, ('127.0.0.1', 60598, 23, 'LOCK', 'b'))
[Proposer 0] Promise Receive PROMISE:0:0:(-1, ('127.0.0.1', 60598, 23, 'LOCK', 'b'))
[Proposer 0] Acceptance Received ACCEPTANCE:0:0:('127.0.0.1', 60598, 23, 'LOCK', 'b')
[Proposer 0] Acceptance Received ACCEPTANCE:0:0:('127.0.0.1', 60598, 23, 'LOCK', 'b')
LockService ID0 (23, 'LOCK', 'b')
[Proposer 0] Consensus Reached ---->RESPOND:-1:-1:(23, 'LOCK', 'b')
[Proposer 0] True
[Proposer 0] 1
[Proposer 0] deque([])
[Proposer 0] Request Receive REQUEST:-1:-1:(22, 'UNLOCK', 'a')
[Proposer 0] Prepared Issued PREPARE:1:0:('127.0.0.1', 42775, 22, 'UNLOCK', 'a')
[Proposer 0] Promise Receive PROMISE:1:0:(-1, ('127.0.0.1', 42775, 22, 'UNLOCK', 'a'))
[Proposer 0] Promise Receive PROMISE:1:0:(-1, ('127.0.0.1', 42775, 22, 'UNLOCK', 'a'))
[Proposer 0] Acceptance Received ACCEPTANCE:1:0:('127.0.0.1', 42775, 22, 'UNLOCK', 'a')
[Proposer 0] Acceptance Received ACCEPTANCE:1:0:('127.0.0.1', 42775, 22, 'UNLOCK', 'a')
LockService ID0 (22, 'UNLOCK', 'a')
[Proposer 0] Consensus Reached ---->RESPOND:-1:-1:(22, 'UNLOCK', 'a')
[Proposer 0] True
[Proposer 0] 2
[Proposer 0] deque([])
[Proposer 0] Request Receive REQUEST:-1:-1:(24, 'UNLOCK', 'b')
[Proposer 0] Prepared Issued PREPARE:2:0:('127.0.0.1', 56774, 24, 'UNLOCK', 'b')
[Proposer 0] Promise Receive PROMISE:2:0:(-1, ('127.0.0.1', 56774, 24, 'UNLOCK', 'b'))
[Proposer 0] Promise Receive PROMISE:2:0:(-1, ('127.0.0.1', 56774, 24, 'UNLOCK', 'b'))
[Proposer 0] Request Receive REQUEST:-1:-1:(21, 'LOCK', 'a')
[Proposer 0] Acceptance Received ACCEPTANCE:2:0:('127.0.0.1', 56774, 24, 'UNLOCK', 'b')
[Proposer 0] Acceptance Received ACCEPTANCE:2:0:('127.0.0.1', 56774, 24, 'UNLOCK', 'b')
LockService ID0 (24, 'UNLOCK', 'b')
[Proposer 0] Consensus Reached ---->RESPOND:-1:-1:(24, 'UNLOCK', 'b')
[Proposer 0] True
[Proposer 0] 3
[Proposer 0] deque([('127.0.0.1', 43353, 21, 'LOCK', 'a')])
[Proposer 0] Prepared Issued PREPARE:3:0:('127.0.0.1', 43353, 21, 'LOCK', 'a')
[Proposer 0] Promise Receive PROMISE:3:0:(-1, ('127.0.0.1', 43353, 21, 'LOCK', 'a'))
[Proposer 0] Promise Receive PROMISE:3:0:(-1, ('127.0.0.1', 43353, 21, 'LOCK', 'a'))
[Proposer 0] Acceptance Received ACCEPTANCE:3:0:('127.0.0.1', 43353, 21, 'LOCK', 'a')
[Proposer 0] Acceptance Received ACCEPTANCE:3:0:('127.0.0.1', 43353, 21, 'LOCK', 'a')
LockService ID0 (21, 'LOCK', 'a')
[Proposer 0] Consensus Reached ---->RESPOND:-1:-1:(21, 'LOCK', 'a')
[Proposer 0] True
[Proposer 0] 4
[Proposer 0] deque([])
[Proposer 0] Packet Ignored PROMISE:1:0:(-1, ('127.0.0.1', 42775, 22, 'UNLOCK', 'a'))
[Proposer 0] Packet Ignored PROMISE:2:0:(-1, ('127.0.0.1', 56774, 24, 'UNLOCK', 'b'))
[Proposer 0] Packet Ignored PROMISE:3:0:(-1, ('127.0.0.1', 43353, 21, 'LOCK', 'a'))

