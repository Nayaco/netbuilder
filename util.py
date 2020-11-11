import jinja2

def render_template(template_path, output_path, data):
    env = jinja2.Environment(loader = jinja2.FileSystemLoader('templates'))
    template = env.get_template(template_path)
    with open(output_path, 'w') as f:
        f.write(template.render(data))
