# PaxosMadeSimpleMadeSimple
# Still not simple enough!

# Developer: Liang Luo & Ming Liu

1. Introduction

2. Design & Implementation
2-1. Assumptions

2-2. Proposer

2-3. Lock service

2-4. Acceptor

3. How to run the experiment

4. Trace Analysis

5. Discussions


This is a somewhat easy toy Paxos implementation.
The Paxos serves as an infraustructure for the application layer protocols.

Each node acts as Acceptor, Proposer and Learner.

We require servers to not skip ahead - i.e. if instance i of Paxos is undone, i+1th cannot start.
We do not maintain logs.
We do allow servers to catch up, i.e., servers can be added to the Paxos group anytime. We support this using a simple approach - the newly added server acts as if it was late in proposing the first rounds. By executing Paxos Basic, these servers are allowed to catch up and compete for the next instance. Note this is exactly the same mechanism that we used to synchronize consensus.
The servers are not eager, meaning they would not usually care about the consensus unless they would like to propose. We choose this property because usually the distinguished leader is alive. If not, some commands need to be flushed (i.e., we use Nops to force servers to catch up to the latest consensus instances).
