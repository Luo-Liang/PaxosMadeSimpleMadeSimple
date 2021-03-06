# PaxosMadeSimpleMadeSimple
## Still not simple enough!
### Developer: Liang Luo & Ming Liu

#### 1. Introduction
In this project, we implement a replicated state machine and use a simple lock service to demonstrate its correctness. Our implemenation is based on the traditional paxos paper. The whole project includes three parts: lock service client, paxos purposer, and paxos acceptor. The lock service client issues lock requests to a distinguised purposer, which uses the paxos algorithm to achieve the consensus among all the acceptors. We take the traditional paxos method that uses two phases protocols on both purposers and acceptors. Our design can handle multiple instances at the same time but can only execute them serially.
The organization of this writeup is as follows: Section 2 talks in details about the design and implementation. Section 3 gives an example on how to use our codes. Section 4 presents some discussion. We end up with a case study and trace analysis.

#### 2. Design & Implementation
##### 2-1. Assumptions

We make the following assumptions:

- There is no message lost in the system;
- Acceptors don't maintain the log and save everything in the stable storage;
- Instances execute in serial;
- No node recovery;
- No message resending;

##### 2-2. purposer

In the original Paxos paper, Lamport purposed that purposers can skip ahead and execute sequences of Paxos requests concurrently. Here we strip off the ability of executing concurrent requests in favor of simplicity.

![Figure1](https://raw.github.com/Luo-Liang/PaxosMadeSimpleMadeSimple/master/figures/concurrentVsSerialPaxos.png)

As shown above, the two implementations are functionally equivalent.

We maintain the notion of a leader purposer, and this purposer is what users direct their requests to. By default, server indexed 0 is the leader purposer, and the clients know all requests should be sent to server indexed 0.

The purposers are not eager, meaning they would not usually care about the consensus results unless they would like to propose. We choose this property because usually the distinguished purposer is alive, so there is no need to spam every purposer with consensus results. 

In times of leader failure, secondary purposers must take place of it. It is the user's responsibility to realize the leader is down (this is usually done by using timeouts - however it is usually impossible to differentiate between "down" and "delayed", but luckily we do not require that). The requests are then delivered to server indexed 1 and so on. 

To make sure duplicated requests are not executed, each request is associated with a sequence number, and servers only execute each command from each client once (though we skip this check in the execution logic for this matter).

purposers, because they are lazy, sometimes need to catch up with the latest happenings in the world. This also happens when new purposers are added. They would learn the previous consensus results by executing Paxos Consensus from instance 0 all the way up to the most recent, and then it tries to purpose whatever it wants in the current instance. Using this, we do not differentiate between newly added servers and lazy servers, and the situations are handled uniformly.

Each request from a user is queued in a server local queue, and is executed in a serial manner when consensus is reached.

Whenever a server realizes a consensus has been reached, it would deliver this value(command of an application service) to an application service. If that service decides this command is runnable, then it will execute it. Otherwise it will tell server to queue it up and try executing later (note all servers must do the same, and it is illegal for some commands to be executed on some servers but not the others). The server will try to propose the first request in the request queue.

A minor optimization is used - sometimes no command in the queue can be executed, so there is no need to keep proposing over and over again. Whenever a command is determined to be un-runnable by the application logic, it is tagged with a 'delay execution bit' conceptually. If everything in the queue is tagged as 'delayed execution', the server will stop purposing until new request arrive. Whenever a request is executed successfully, the 'delay execution bit' is removed from all requests in the queue and are therefore proposed again later.

One minor consequence of this is that the commands are executed out of order in the sense that the command from the same client to the same server may be out of order as well. However this is not a big issue at all: (1) the internet is itself out of order as we are using UDPs. (2) the client can simply execute in lock step for the commands that cannot be executed out of order. (3) we can just enforce the servers to not reorder commands from the same client to the same server. We took neither of the options and decided to let it be.


##### 2-3. Acceptor
The data structure of the acceptor includes three queues: RequestNumberQueue, ConsensusQueue, and ProposalQueue. The RequestNumberQueue saves the highest accepted proposal number for each instance while the ConsensusQueue and ProposalQueue record the accepted value and promised proposal number of each instance.

The protocol of the acceptor works as follows:
(a) When it receives the PREPARE request, it firstly compares with its promised proposal number. If it's higher, the acceptor will send a promise request with a tuple <highest accepted number, accepted value>. Note that the highest accepted number is -1 in the beginning. Meanwhile, it also updates its ProposalQueue. If not, the acceptor will send a DENIAL request.
(b) When it receives the ACCEPT request, it also compared with its promised pproposal number. If it's higher or equal, the acceptor will (1) accept this value, (2) send the acceptance knowledgement to the purposer, and (3)update its RequestNumberQueue and ConsensusQueue. If not, the acceptor will send a DENIAL request.

#### 3. Running the experiments
Our codes are quite easy to use. We provide two scripts: run.sh and test.sh.
run.sh --> Start three servers. Each server has three roles: purposer, acceptor and learner
test.sh --> Choose running scenarios. We develop 7 scenarios to select. By sh test.sh, you can see detailed information. By sh test.sh <option>, you can run the case you choose.

#### 4. Discussions
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

Lock() will only return when it is successfully acquired, while Unlock() returns immediately after consensus.

##### 6.1 Trace Analysis

Here is a simple trace resulted from executing the following client commands,

    printf "REQUEST:-1:-1:(21,'LOCK','a')" | nc -u 127.0.0.1 29367 &
    printf "REQUEST:-1:-1:(22,'UNLOCK','a')" | nc -u 127.0.0.1 29367 &
	printf "REQUEST:-1:-1:(23,'LOCK','b')" | nc -u 127.0.0.1 29367 &
	printf "REQUEST:-1:-1:(24,'UNLOCK','b')" | nc -u 127.0.0.1 29367 &

This instantiates 4 clients and send interleaved LOCK and UNLOCK commands. The expected result is that all 4 commands are executed, though order may vary.

To give a little bit of background, 3 Paxos nodes are used, and they are located at *localhost:29367-29369*, and only print outs for purposer 0 is shown to avoid distraction.

Trace is analyzed in-line. And the format is shown below:

-> *CommandType*:*InstanceId*:*RequestNumber*:*(value)* <- 
> [purposer 0] Request Receive REQUEST:-1 : -1:(22, 'UNLOCK', 'a')												  <br/>
// purposer has received the request to unlock a.																  <br/>
> [purposer 0] Prepared Issued PREPARE:0:0:('127.0.0.1', 46995, 22, 'UNLOCK', 'a')								  <br/>
> [purposer 0] Promise Receive PROMISE:0:0:(-1, ('127.0.0.1', 46995, 22, 'UNLOCK', 'a'))						  <br/>
> [purposer 0] Promise Receive PROMISE:0:0:(-1, ('127.0.0.1', 46995, 22, 'UNLOCK', 'a'))						  <br/>
// A majority of promises are received. There is no need to wait on the other ones. Issue Accept messages.		  <br/>
> [purposer 0] Acceptance Received ACCEPTANCE:0:0:('127.0.0.1', 46995, 22, 'UNLOCK', 'a')						  <br/>
> [purposer 0] Acceptance Received ACCEPTANCE:0:0:('127.0.0.1', 46995, 22, 'UNLOCK', 'a')						  <br/>
// A majority of acceptances are received. 																  <br/>
> LockService ID0 (22, 'UNLOCK', 'a') 																		  <br/>
//A consensus has reached, so deliver this to application service. 											  <br/>
//The following are almost identical.                            											  <br/>
> [purposer 0] Consensus Reached ---->RESPOND:-1 : -1:(22, 'UNLOCK', 'a')										  <br/>
> [purposer 0] Request Receive REQUEST:-1 : -1:(23, 'LOCK', 'b')												  <br/>
> [purposer 0] Prepared Issued PREPARE:1:0:('127.0.0.1', 40108, 23, 'LOCK', 'b')								  <br/>
> [purposer 0] Promise Receive PROMISE:1:0:(-1, ('127.0.0.1', 40108, 23, 'LOCK', 'b'))							  <br/>
> [purposer 0] Request Receive REQUEST:-1 : -1:(21, 'LOCK', 'a')												  <br/>
> [purposer 0] Promise Receive PROMISE:1:0:(-1, ('127.0.0.1', 40108, 23, 'LOCK', 'b'))							  <br/>
> [purposer 0] Request Receive REQUEST:-1 : -1:(24, 'UNLOCK', 'b')												  <br/>
> [purposer 0] Acceptance Received ACCEPTANCE:1:0:('127.0.0.1', 40108, 23, 'LOCK', 'b')							  <br/>
> [purposer 0] Acceptance Received ACCEPTANCE:1:0:('127.0.0.1', 40108, 23, 'LOCK', 'b')							  <br/>
> LockService ID0 (23, 'LOCK', 'b')																				  <br/>
> [purposer 0] Consensus Reached ---->RESPOND:-1 : -1:(23, 'LOCK', 'b')											  <br/>
> [purposer 0] Prepared Issued PREPARE:2:0:('127.0.0.1', 59905, 21, 'LOCK', 'a')								  <br/>
> [purposer 0] Packet Ignored PROMISE:0:0:(-1, ('127.0.0.1', 46995, 22, 'UNLOCK', 'a'))							  <br/>
// A dated Promise from Instance 0 Request 0 has received, and we just ignored it.									  <br/>
> [purposer 0] Packet Ignored PROMISE:1:0:(-1, ('127.0.0.1', 40108, 23, 'LOCK', 'b'))							  <br/>
> [purposer 0] Promise Receive PROMISE:2:0:(-1, ('127.0.0.1', 59905, 21, 'LOCK', 'a'))							  <br/>
> [purposer 0] Promise Receive PROMISE:2:0:(-1, ('127.0.0.1', 59905, 21, 'LOCK', 'a'))							  <br/>
> [purposer 0] Acceptance Received ACCEPTANCE:2:0:('127.0.0.1', 59905, 21, 'LOCK', 'a')							  <br/>
> [purposer 0] Acceptance Received ACCEPTANCE:2:0:('127.0.0.1', 59905, 21, 'LOCK', 'a')							  <br/>
> LockService ID0 (21, 'LOCK', 'a')																				  <br/>
> [purposer 0] Consensus Reached ---->RESPOND:-1 : -1:(21, 'LOCK', 'a')						<br/>
> [purposer 0] Prepared Issued PREPARE:3:0:('127.0.0.1', 56120, 24, 'UNLOCK', 'b')			<br/>
> [purposer 0] Promise Receive PROMISE:3:0:(-1, ('127.0.0.1', 56120, 24, 'UNLOCK', 'b'))	<br/>
> [purposer 0] Promise Receive PROMISE:3:0:(-1, ('127.0.0.1', 56120, 24, 'UNLOCK', 'b'))	<br/>
> [purposer 0] Acceptance Received ACCEPTANCE:3:0:('127.0.0.1', 56120, 24, 'UNLOCK', 'b')	<br/>
> [purposer 0] Acceptance Received ACCEPTANCE:3:0:('127.0.0.1', 56120, 24, 'UNLOCK', 'b')	<br/>
> LockService ID0 (24, 'UNLOCK', 'b')														<br/>
> [purposer 0] Consensus Reached ---->RESPOND:-1 : -1:(24, 'UNLOCK', 'b')					<br/>
> [purposer 0] Packet Ignored PROMISE:2:0:(-1, ('127.0.0.1', 59905, 21, 'LOCK', 'a'))		<br/>
> [purposer 0] Packet Ignored PROMISE:3:0:(-1, ('127.0.0.1', 56120, 24, 'UNLOCK', 'b'))		<br/>
																							
As another illustration, consider the following command and its resulting trace.			
																							
    printf "REQUEST:-1:-1:(25,'LOCK','a')" | nc -u 127.0.0.1 29367 &						
	printf "REQUEST:-1:-1:(26,'UNLOCK','a')" | nc -u 127.0.0.1 29367 &
	printf "REQUEST:-1:-1:(27,'LOCK','b')" | nc -u 127.0.0.1 29367 &
	printf "REQUEST:-1:-1:(28,'UNLOCK','b')" | nc -u 127.0.0.1 29367 &

	printf "REQUEST:-1:-1:(29,'LOCK','a')" | nc -u 127.0.0.1 29368 &
	printf "REQUEST:-1:-1:(30,'UNLOCK','a')" | nc -u 127.0.0.1 29368 &
	printf "REQUEST:-1:-1:(31,'LOCK','b')" | nc -u 127.0.0.1 29368 &
	printf "REQUEST:-1:-1:(32,'UNLOCK','b')" | nc -u 127.0.0.1 29368 &

	printf "REQUEST:-1:-1:(33,'LOCK','a')" | nc -u 127.0.0.1 29369 &
	printf "REQUEST:-1:-1:(34,'UNLOCK','a')" | nc -u 127.0.0.1 29369 &
	printf "REQUEST:-1:-1:(35,'LOCK','b')" | nc -u 127.0.0.1 29369 &
	printf "REQUEST:-1:-1:(36,'UNLOCK','b')" | nc -u 127.0.0.1 29369 &

Here we send multiple commands to multiple servers. We stripped off the traces from the servers and only left the print outs from lock service. This is the best way to evaluate whether all paxos nodes are executing the exact same sequence of commands.

> LockService ID0 (25, 'LOCK', 'a')		   <br/>
> LockService ID0 (27, 'LOCK', 'b')		   <br/>
> LockService ID0 (28, 'UNLOCK', 'b')	   <br/>
> LockService ID1 (25, 'LOCK', 'a')		   <br/>
> LockService ID1 (27, 'LOCK', 'b')		   <br/>
> LockService ID2 (25, 'LOCK', 'a')		   <br/>
> LockService ID0 (26, 'UNLOCK', 'a') 	   <br/>
> LockService ID1 (28, 'UNLOCK', 'b')	   <br/>
> LockService ID2 (27, 'LOCK', 'b')		   <br/>
> LockService ID1 (26, 'UNLOCK', 'a')	   <br/>
> LockService ID1 (30, 'UNLOCK', 'a')	   <br/>
> LockService ID2 (28, 'UNLOCK', 'b')	   <br/>
> LockService ID1 (31, 'LOCK', 'b')		   <br/>
> LockService ID2 (26, 'UNLOCK', 'a')	   <br/>
> LockService ID1 (29, 'LOCK', 'a')		   <br/>
> LockService ID2 (30, 'UNLOCK', 'a')	   <br/>
> LockService ID1 (32, 'UNLOCK', 'b')	   <br/>
> LockService ID2 (31, 'LOCK', 'b')		   <br/>
> LockService ID2 (29, 'LOCK', 'a')		   <br/>
> LockService ID2 (32, 'UNLOCK', 'b')	   <br/>
> LockService ID2 (33, 'LOCK', 'a')		   <br/>
> LockService ID2 (35, 'LOCK', 'b')		   <br/>
> LockService ID2 (34, 'UNLOCK', 'a')	   <br/>
> LockService ID2 (36, 'UNLOCK', 'b')	   <br/>
> LockService ID2 (33, 'LOCK', 'a')		   <br/>

To make sense of this trace, let's re-arrange them with a node-centric view instead of time-centric view. The number denoted below means packet sequence number. We use one sequence to identify an unique packet across all clients in order to analyze this better.

LockService ID0: 25-27-28-26 <br/>
LockService ID1: 25-27-28-26-30-31-29-32 <br/>
LockService ID2: 25-27-28-26-30-31-29-32-33-35-34-36-33 <br/>

Note that according to the lazy purposer design, since node0 and node1 have no more requests, they stopped learning consensus values when they finished processing their requests. The semantic meaning of this trace is obvious. Note the interest part here is request 33 is attempted twice because it cannot be executed due to lock A is unavailable at the first time. It is subsequently attempted.

#### Limitations
There is a case where the catch-up server needs to purpose from 0 to a certain high number before it can learn the consensus for a past instance. This is due to the fact we don't differentiate between newly added server and a slow server.
