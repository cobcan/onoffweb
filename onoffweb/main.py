from threading import Thread, Event
from flask import Flask, render_template, request
from wakeonlan import send_magic_packet
from icmplib import ping
from paramiko import SSHClient,  AutoAddPolicy, RSAKey
import yaml, os, logging, json, time, sys
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    level=logging.INFO,
)


app = Flask(__name__)

# GLOBAL VARIABLES
server_states={} # Initial states of the servers
## CONSTANTS (will be set from a cofigfile)
LIST_SERVERS_NAMES=[] #list of all the server names in config.yml
MACS={} # dictionary of name:mac for each server
ADDRESSES={} # dictionary of name:ip for each server
SSH_USERS={}
SSH_KEY_FILENAME={}
WEB="index.html"

def check_servers(run_event):
        while run_event.is_set():
            for server_name in LIST_SERVERS_NAMES:
                server = ping(ADDRESSES[server_name], count=1, interval=0.5,timeout=2)
                #logging.info(rtt)
                if server.is_alive:
                    server_states[server_name] = '1'
                else:
                    server_states[server_name] = '0'
            time.sleep(5)



def awake_server(server_name):
    logging.info("Wake-On-LAN: "+ADDRESSES[server_name] + ' -- ' + MACS[server_name] )
    try:
        send_magic_packet(MACS[server_name])
    except Exception as e:
        return e
def suspend_server(server_name):
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    host=ADDRESSES[server_name]
    user=SSH_USERS[server_name]
    key_filename=SSH_KEY_FILENAME[server_name]
    try:
        pkey = RSAKey.from_private_key_file(key_filename)
        logging.info("Connection to "+host+" via SSH")
        ssh.connect(host, username=user, pkey=pkey, look_for_keys=False, allow_agent=False, timeout=2)
        logging.info("Shutting down "+host)
        stdin, stdout, stderr = ssh.exec_command('systemctl suspend')
        logging.info(stdout.read())
    except Exception as e:
        logging.info(str(e))
        return e
    finally:
        logging.info("Closing connection to "+host+" via SSH")
        ssh.close()

@app.route('/server_states')
def get_server_states():
    return json.dumps(server_states, indent=4)


@app.route('/')
def my_form():
    return render_template(WEB, list_servers=LIST_SERVERS_NAMES) # This should be the name of your HTML file

@app.route('/', methods=['POST'])
def post():
    #time.sleep(0.3) # limit how many request can be done
    for server_name in LIST_SERVERS_NAMES:
        if 'submit_'+server_name in request.form:
            if request.form['submit_'+server_name] == "ON":
                error=awake_server(server_name)
                text="Waking Up"
                return render_template(WEB, list_servers=LIST_SERVERS_NAMES, selected_server=server_name, on=True, text=text, error=error)
            if request.form['submit_'+server_name] == "OFF":
                error=suspend_server(server_name)
                text="Shutting Down"
                return render_template(WEB, list_servers=LIST_SERVERS_NAMES,selected_server=server_name, on=False,  dict_servers_states=server_states, text=text, error=error)



host = os.environ.get("WOLWEB_HOST", "0.0.0.0")
port = os.environ.get("WOLWEB_PORT", "8181")
config_file = os.environ.get("WOLWEB_CONFIG_FILE", "./config.yml")

with open(config_file, 'r') as file:
    config = yaml.safe_load(file)

for server in config["servers"]:
    LIST_SERVERS_NAMES.append(server["name"])
    MACS[server["name"]] = server["mac"]
    ADDRESSES[server["name"]] = server["address"]
    SSH_USERS[server["name"]] = server["ssh_user"]
    SSH_KEY_FILENAME[server["name"]] = server["ssh_key_filename"]
    server_states[server["name"]]= '0'

if __name__ == '__main__':
    try:
        run_event = Event()
        run_event.set()
        thread = Thread(target=check_servers,args= (run_event,))
        thread.start()
        app.run(host=host, port=port ,threaded=True) # This line does not iterate until i kill the app
        ## this must be after the app to kill all the thread when the app dies
        run_event.clear()
        print("Killing all threads")
        thread.join()
    except Exception as e:
        logging.error(e)
        run_event.clear()
        print("Killing all threads")
        thread.join()
       
        
