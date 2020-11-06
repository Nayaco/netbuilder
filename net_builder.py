import subprocess
import jinja2
# process = subprocess.Popen(['echo', 'More output'],
#                      stdout=subprocess.PIPE, 
#                      stderr=subprocess.PIPE)
# stdout, stderr = process.communicate()
# print(stdout, stderr)

env = jinja2.Environment(loader = jinja2.FileSystemLoader('./'))

template = env.get_template('fabric-ca-server-config.yaml')
output = template.render(ca_port = 7054, 
                ca_debug = False, 
                ca_name = 'OrdererCA',
                ca_cn = 'example.com')
