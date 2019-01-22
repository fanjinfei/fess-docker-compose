
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
