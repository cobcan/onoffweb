# onoffweb
Declarative web in python Flask to power up and power off your servers with wakeonlan and ssh 

## How to use

This app reads from a config.yml file. You can execute directly the main.py or deploy it with docker.
There are 3 env variables:
- WOLWEB_HOST (address where the web will be localted)
- WOLWEB_PORT (port that the web will use)
- WOLWEB_COFIG_FILE (filepath of the config.yml)
