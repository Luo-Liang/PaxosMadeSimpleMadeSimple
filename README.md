# PaxosMadeSimpleMadeSimple
# Still not simple enough!
# Developer: Liang Luo & Ming Liu

1. Introduction
In this project, we implement a replicated state machine and use a simple lock service to demonstrate its correctness. Our implemenation is based on the traditional paxos paper. The whole project includes three parts: lock service client, paxos proposer, and paxos acceptor. The lock service client issues lock requests to a distinguised proposer, which uses the paxos algorithm to achieve the consensus among all the acceptors. We take the traditional paxos method that uses two phases protocols on both proposers and acceptors. Our design can handle multiple instances at the same time but can only execute them serially.
The organization of this writeup is as follows: Section 2 talks in details about the design and implementation. Section 3 gives an example on how to use our codes. Section 4 presents some discussion. We end up with a case study and trace analysis.

2. Design & Implementation
2-1. Assumptions
We make the following assumptions:
(1) There is no message lost in the system;
(2) Acceptors don't maintain the log and save everything in the stable storage;
(3) Instances execute in serial;
(4) No node recovery;
(5) No message resending;

##### 2-2. Proposer

In the original Paxos paper, Lamport purposed that proposers can skip ahead and execute sequences of Paxos requests concurrently. Here we strip off the ability of executing concurrent requests in favor of simplicity.

![Main Window](https://raw.github.com/Luo-Liang/PaxosMadeSimpleMadeSimple/figures/concurrentVsSerialPaxos.png)

As shown above, the two implementations are functionally equivalent.

We maintain the notion of a leader proposer, and this proposer is what users direct their requests to. By default, server indexed 0 is the leader proposer, and the clients know all requests should be sent to server indexed 0.

The proposers are not eager, meaning they would not usually care about the consensus results unless they would like to propose. We choose this property because usually the distinguished proposer is alive, so there is no need to spam every proposer with consensus results. 

In times of leader failure, secondary proposers must take place of it. It is the user's responsibility to realize the leader is down (this is usually done by using timeouts - however it is usually impossible to differentiate between "down" and "delayed", but luckily we do not require that). The requests are then delivered to server indexed 1 and so on. 

To make sure duplicated requests are not executed, each request is associated with a sequence number, and servers only execute each command from each client once (though we skip this check in the execution logic for this matter).

Proposers, because they are lazy, sometimes need to catch up with the latest happenings in the world. This also happens when new proposers are added. They would learn the previous consensus results by executing Paxos Consensus from instance 0 all the way up to the most recent, and then it tries to purpose whatever it wants in the current instance. Using this way, we do not differentiate between newly added servers and lazy servers, and the situations are handled uniformly.

Each request from a user is queued in a server local queue, and is executed in a serial manner when consensus is reached.

Whenever a server realizes a consensus has been reached, it would deliver this value(command of an application service) to an application service. If that service decides this command is runnable, then it will execute it. Otherwise it will tell server to queue it up and try executing later (note all servers must do the same, and it is illegal for some commands to be executed on some servers but not the others). The server will try to propose the first request in the request queue.

A minor optimization is used - sometimes no command in the queue can be executed, so there is no need to keep proposing over and over again. Whenever a command is determined to be un-runnable by the application logic, it is tagged with a 'delay execution bit' conceptually. If everything in the queue is tagged as 'delay execution bit', the server will stop purposing until new request arrive. Whenever a request is executed successfully, the 'delay execution bit' is removed from all requests in the queue and are therefore proposed again later.

One minor consequence of this is that the commands are executed out of order in the sense that the command from the same client to the same server may be out of order as well. However this is not a big issue at all: (1) the internet is itself out of order as we are using UDPs. (2) the client can simply execute in lock step for the commands that cannot be executed out of order. (3) we can just enforce the servers to not reorder commands from the same client to the same server. We took neither of the options and decided to let it be.


2-4. Acceptor
The data structure of the acceptor includes three queues: RequestNumberQueue, ConsensusQueue, and ProposalQueue. The RequestNumberQueue saves the highest accepted proposal number for each instance while the ConsensusQueue and ProposalQueue record the accepted value and promised proposal number of each instance.

The protocol of the acceptor works as follows:
(a) When it receives the PREPARE request, it firstly compares with its promised proposal number. If it's higher, the acceptor will send a promise request with a tuple <highest accepted number, accepted value>. Note that the highest accepted number is -1 in the beginning. Meanwhile, it also updates its ProposalQueue. If not, the acceptor will send a DENIAL request.
(b) When it receives the ACCEPT request, it also compared with its promised pproposal number. If it's higher or equal, the acceptor will (1) accept this value, (2) send the acceptance knowledgement to the proposer, and (3)update its RequestNumberQueue and ConsensusQueue. If not, the acceptor will send a DENIAL request.

3. How to run the experiment
Our codes are quite easy to use. We provide two scripts: run.sh and test.sh.
run.sh --> Start three servers. Each server has three roles: proposer, acceptor and learner
test.sh --> Choose running scenarios. We develop 7 scenarios to select. By sh test.sh, you can see detailed information. By sh test.sh <option>, you can run the case you choose.

4. Discussions
(1) Why the acceptor maintain the queue instead of just one variable?
Because we'd like to deal with multiple instances.
(2) Why do have the denial request?
The denial request is used to indicate the proposal whether the proposal number is smaller than the acceptor's expectation.

#### 5. CASE STUDY: Lock service on top of Paxos

We use Lock Service to demonstrate Paxos. Notice this Paxos implementation is by no means coupled with this specific service. As long as proper interfaces are implemented, any service can be used as drop-in replacement.

The Lock Service is dumb in the sense that it does no ownership checking, dead-lock prevention or any fancy things that may ever  be desired in a real world lock service.

The semantic of the lock service is very simple:

-> (*Uid*,*Seq*,*action*,*object*) <-

where: 

- **Uid** is basically the id of the client
- **seq** is the sequence number of request for that client
- **action** is either **lock** or **unlock**
- **object** is the name of the lock to be operated on

Lock will only return when it is successfully acquired, while unlock returns immediately after consensus.

##### 6.1 Trace Analysis

