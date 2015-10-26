# Paxos Made Simple Made Simpler
## Still not simple enough!
### Developer: Liang Luo & Ming Liu

This is a somewhat easy toy Paxos implementation.
The Paxos serves as an infraustructure for the application layer protocols.

#### 1. Introduction 

#### 2. Design & Implementation

##### 2.1 Assumptions

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


##### 2-4. Acceptor

##### 3. CASE STUDY: Lock service on top of Consensus

We use Lock Service to demonstrate Paxos. Notice this Paxos implementation is by no means coupled with this specific service. As long as proper interfaces are implemented, any service can be used as drop-in replacement.

The Lock Service is dumb in the sense that it does no ownership checking, dead-lock prevention or any fancy things that may be ever desired in a real world lock service.

The semantic of the lock service is very simple:

(*Uid*,*Seq*,*action*,*object*)

#### 4. How to run the experiment

#### 5. Trace Analysis

#### 6. Discussions



Each node acts as Acceptor, Proposer and Learner.

We require servers to not skip ahead - i.e. if instance i of Paxos is undone, i+1th cannot start.
We do not maintain logs.
We do allow servers to catch up, i.e., servers can be added to the Paxos group anytime. We support this using a simple approach - the newly added server acts as if it was late in proposing the first rounds. By executing Paxos Basic, these servers are allowed to catch up and compete for the next instance. Note this is exactly the same mechanism that we used to synchronize consensus.

