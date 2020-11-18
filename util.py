import jinja2

def msp_autofill(data):
    data['orderer']['orderer_msp'] = data['orderer']['orderer_name'] + 'MSP'
    for org in data['peerorgs']: 
        org['peer_msp'] = org['peer_name'] + 'MSP'
    for channel in data['channels']:
        channel['msps'] = []
        for org in channel['peerorgs']:
            channel['msps'].append(org + 'MSP')

def render_template(template_path, output_path, data):
    env = jinja2.Environment(loader = jinja2.FileSystemLoader('templates'))
    template = env.get_template(template_path)
    with open(output_path, 'w') as f:
        f.write(template.render(data))