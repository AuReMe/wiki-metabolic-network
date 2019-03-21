SHELL := /bin/bash 
# very important to stop make from deleting intermediate files
NETWORK_NAME = 'wiki-metabolic'

#---------------
#TODO
init:
	@echo "------>Initialization of wiki-metabolic service."
	@sudo docker-compose -p $(NETWORK_NAME) up -d
#---------------

#---------------
#TODO
pause:
	@echo "------>Pause wiki-metabolic service."
	@sudo docker-compose -p $(NETWORK_NAME) pause
#---------------

#---------------
#TODO
unpause:
	@echo "------>Unpause wiki-metabolic serivce."
	@sudo docker-compose -p $(NETWORK_NAME) unpause
#---------------


#---------------
#TODO
remove:
	@echo "------>Remove wiki-metabolic serivce."
	@sudo docker-compose -p $(NETWORK_NAME) down
#---------------







#--------------------------------------------------------------
#---------------
#TODO
build:
	@echo "------>Build wiki-metabolic-network-img."
	@sudo docker build --force-rm -t docker.io/dyliss/wiki-metabolic-network-img .
#---------------

