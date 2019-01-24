
Original dockerfile from: https://hub.docker.com/r/codelibs/fess/

1. build. (if behind proxy, run "export DOCKER_CONFIG=./conf", edit the config.json)
  #docker build --force-rm  -t codelibs/fess:fess12.4.3 ./

2. run
   docker-compose up -d
   
3. stop
    docker-compose stop search

4. save FESS config (it will be reloaded on service start)
  4.1 http://localhost:8080/admin, config via GUI
  4.2 #docker exec -it fess-docker_search_1_535c4  /bin/bash OR
      #docker-compose exec search /bin/bash
      then 
      #/var/lib/elasticsearch/bin/save_config.sh

If run on CentOS:
5. change docker default data directory:
  /etc/fstab: UUID=<ls -l /dev/disks/by-uuid> /data ext4 defaults,user 0 0
  File /lib/systemd/system/docker.service: ExecStart=/usr/bin/docker daemon -g /new/path/docker -H fd://
  systemctl stop docker&& systemctl daemon-reload && systemctl start docker


6. prepare permission for docker
  # sudo usermod -aG docker <user name> -- need to logout
  #
  # mkdir -p data/nodes
  # mkdir -p data/config
  # sudo chgrp -R 1000 ./data
  # sudo chmod -R 0777 ./data -- fix later
