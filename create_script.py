import util
import os

def create_registerEnroll(target_dir, data):
    if not os.path.exists(target_dir): 
        os.mkdir(target_dir)
    if not os.path.exists(os.path.join(target_dir, 'organizations')): 
        os.mkdir(os.path.join(target_dir, 'organizations'))
    if not os.path.exists(os.path.join(target_dir, 'organizations', 'fabric-ca')):
        os.mkdir(os.path.join(target_dir, 'organizations', 'fabric-ca'))
    util.render_template('organizations/fabric-ca/registerEnroll.sh',
        os.path.join(target_dir, 'organizations', 'fabric-ca', 'registerEnroll.sh'), data)

def create_envVars(target_dir, data):
    if not os.path.exists(target_dir): 
        os.mkdir(target_dir)
    if not os.path.exists(os.path.join(target_dir, 'scripts')): 
        os.mkdir(os.path.join(target_dir, 'scripts'))
    util.render_template('scripts/envVars.sh',
        os.path.join(target_dir, 'scripts', 'envVars.sh'), data)
