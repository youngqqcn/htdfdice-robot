start:
	@nohup python3 -u robot.py > output.log 2>&1 &

upload:
	@scp -r -P52113 -i /data2/work/hetbi-style.pem  /data2/work/htdfdice-robot root@161.117.36.227:/data/

stop:
	@kill -9  $$(ps aux | grep '[p]ython3 -u robot.py' | awk '{print $$2}')