import jinja2

def data_autofill(data):
    for channel in data['channels']:
        channel['msps'] = []
        channel['peerorg_nodes'] = [0] * len(channel['peerorgs'])
        for org in channel['peerorgs']:
            channel['msps'].append(org + 'MSP')
    data['orderer']['orderer_msp'] = data['orderer']['orderer_name'] + 'MSP'
    for org in data['peerorgs']: 
        org['peer_msp'] = org['peer_name'] + 'MSP'
        for channel in data['channels']:
            try:
                channel['peerorg_nodes'][channel['peerorgs'].index(org['peer_name'])] = org['peer_nodes']
            except ValueError:
                pass
            
def render_template(template_path, output_path, data):
    env = jinja2.Environment(loader = jinja2.FileSystemLoader('weaver-templates'))
    template = env.get_template(template_path)
    with open(output_path, 'w') as f:
        f.write(template.render(data))