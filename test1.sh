#printf "REQUEST:-1:-1:(0,'LOCK','a')\nREQUEST:-1:-1:(1,'LOCK','b')\nREQUEST:-1:-1:(2,'LOCK','c'\nREQUEST:-1:-1:(3,'UNLOCK','a'\nREQUEST:-1:-1:(4,'UNLOCK','b')\nREQUEST:-1-1:(5,'UNLOCK','c')" | nc -u 127.0.0.1 29367 &
#printf "REQUEST:-1:-1:(0,'LOCK','a')\nREQUEST:-1:-1:(1,'LOCK','b')\nREQUEST:-1:-1:(2,'LOCK','c'\nREQUEST:-1:-1:(3,'UNLOCK','a'\nREQUEST:-1:-1:(4,'UNLOCK','b')\nREQUEST:-1-1:(5,'UNLOCK','c')" | nc -u 127.0.0.1 29367 &
#printf "REQUEST:-1:-1:(1,'LOCK','a')" | nc -u 127.0.0.1 29367 &
#printf "REQUEST:-1:-1:(2,'LOCK','a')" | nc -u 127.0.0.1 29368 &
#printf "REQUEST:-1:-1:(3,'UNLOCK','a')" | nc -u 127.0.0.1 29369 &
#printf "REQUEST:-1:-1:(5,'LOCK','a')" | nc -u 127.0.0.1 29367 &
printf "REQUEST:-1:-1:(4,'UNLOCK','a')" | nc -u 127.0.0.1 29369 &
