#!/bin/bash
if [ $# -ne 1 ]
then
	echo "Usage:" $0 "<option>"
	echo "Option 0: LOCK from the same host"
	echo "Option 1: LOCK from different hosts"
	echo "Option 2: UNLOCK from the same host"
	echo "Option 3: UNLOCK from different hosts"
	echo "Option 4: LOCK/UNLOCK from the same host"
	echo "Option 5: LOCK/UNLOCK from different hosts"
	echo "Option 6: Random"
	exit
fi

if [ $1 -eq 0 ]
then
	printf "REQUEST:-1:-1:(1,'LOCK','a')" | nc -u 127.0.0.1 29367 &
	printf "REQUEST:-1:-1:(2,'LOCK','a')" | nc -u 127.0.0.1 29367 &
	printf "REQUEST:-1:-1:(3,'LOCK','b')" | nc -u 127.0.0.1 29367 &
	printf "REQUEST:-1:-1:(4,'LOCK','b')" | nc -u 127.0.0.1 29367 &
elif [ $1 -eq 1 ]
then
	printf "REQUEST:-1:-1:(5,'LOCK','a')" | nc -u 127.0.0.1 29367 &
	printf "REQUEST:-1:-1:(6,'LOCK','a')" | nc -u 127.0.0.1 29368 &
	printf "REQUEST:-1:-1:(7,'LOCK','a')" | nc -u 127.0.0.1 29369 &

	printf "REQUEST:-1:-1:(8,'LOCK','b')" | nc -u 127.0.0.1 29367 &
	printf "REQUEST:-1:-1:(9,'LOCK','b')" | nc -u 127.0.0.1 29368 &
	printf "REQUEST:-1:-1:(10,'LOCK','b')" | nc -u 127.0.0.1 29369 &
elif [ $1 -eq 2 ]
then
	printf "REQUEST:-1:-1:(11,'UNLOCK','a')" | nc -u 127.0.0.1 29367 &
	printf "REQUEST:-1:-1:(12,'UNLOCK','a')" | nc -u 127.0.0.1 29367 &
	printf "REQUEST:-1:-1:(13,'UNLOCK','b')" | nc -u 127.0.0.1 29367 &
	printf "REQUEST:-1:-1:(14,'UNLOCK','b')" | nc -u 127.0.0.1 29367 &
elif [ $1 -eq 3 ]
then
	printf "REQUEST:-1:-1:(15,'UNLOCK','a')" | nc -u 127.0.0.1 29367 &
	printf "REQUEST:-1:-1:(16,'UNLOCK','a')" | nc -u 127.0.0.1 29368 &
	printf "REQUEST:-1:-1:(17,'UNLOCK','a')" | nc -u 127.0.0.1 29369 &

	printf "REQUEST:-1:-1:(18,'UNLOCK','b')" | nc -u 127.0.0.1 29367 &
	printf "REQUEST:-1:-1:(19,'UNLOCK','b')" | nc -u 127.0.0.1 29368 &
	printf "REQUEST:-1:-1:(20,'UnLOCK','b')" | nc -u 127.0.0.1 29369 &
elif [ $1 -eq 4 ]
then
	printf "REQUEST:-1:-1:(21,'LOCK','a')" | nc -u 127.0.0.1 29367 &
	printf "REQUEST:-1:-1:(22,'UNLOCK','a')" | nc -u 127.0.0.1 29367 &
	printf "REQUEST:-1:-1:(23,'LOCK','b')" | nc -u 127.0.0.1 29367 &
	printf "REQUEST:-1:-1:(24,'UNLOCK','b')" | nc -u 127.0.0.1 29367 &
elif [ $1 -eq 5 ]
then
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
elif [ $1 -eq 6 ]
then
	printf "REQUEST:-1:-1:(37,'LOCK','a')" | nc -u 127.0.0.1 29367 &
	printf "REQUEST:-1:-1:(38,'LOCK','a')" | nc -u 127.0.0.1 29368 &
	printf "REQUEST:-1:-1:(39,'UNLOCK','a')" | nc -u 127.0.0.1 29369 &
	printf "REQUEST:-1:-1:(40,'UNLOCK','a')" | nc -u 127.0.0.1 29369 &

	printf "REQUEST:-1:-1:(41,'LOCK','b')" | nc -u 127.0.0.1 29367 &
	printf "REQUEST:-1:-1:(42,'LOCK','b')" | nc -u 127.0.0.1 29368 &
	printf "REQUEST:-1:-1:(43,'UNLOCK','b')" | nc -u 127.0.0.1 29369 &
	printf "REQUEST:-1:-1:(44,'UNLOCK','b')" | nc -u 127.0.0.1 29369 &

	printf "REQUEST:-1:-1:(45,'LOCK','a')" | nc -u 127.0.0.1 29367 &
	printf "REQUEST:-1:-1:(46,'LOCK','a')" | nc -u 127.0.0.1 29368 &
	printf "REQUEST:-1:-1:(47,'UNLOCK','a')" | nc -u 127.0.0.1 29369 &
	printf "REQUEST:-1:-1:(48,'UNLOCK','a')" | nc -u 127.0.0.1 29369 &
else
	echo "Unkown Option"
fi
