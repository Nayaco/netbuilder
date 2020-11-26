import subprocess, os, sys, stat, time

class LedgerBootError(RuntimeError):
    def __init__(self, msg):
        self.msg = msg

class LedgerController:
    target_path = './'
    environment = {}
    runtime_env = os.environ.copy() 
    stdout = ''
    stderr = ''
    logfile = os.getcwd() + '/log.txt'
    initialed = False

    data = {}
    def __init__(self, target_path='./', env={}, logfile=os.getcwd() + '/log.txt', data={}): 
        self.target_path = target_path
        self.environment = env
        self.runtime_env = {**self.runtime_env, **self.environment}
        self.logfile = logfile
        self.data = data

    def set_env(self, env_key, env_val=''): 
        self.environment[env_key] = env_val
        self.runtime_env[env_key] = env_val
    
    def _run_command(self, command='pwd', args=[]):
        process_command = [command] + args
        process = subprocess.Popen(
                process_command,
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                env=self.runtime_env)
        with open(self.logfile, 'w') as log:
            for line in process.stdout:
                sys.stdout.write(line.decode('utf-8'))
                log.write(line.decode('utf-8'))
        _stdout, _stderr = process.communicate()
        self.stdout = _stdout.decode('utf-8')
        return process.returncode

    def init_docker(self): 
        if(self._run_command(command='docker', args=['volume', 'ls', '-q'])):
            return 1
        volumes = self.stdout.split('\n')
        volumes.remove('')
        if(len(volumes) == 0):
            self.initialed = True
            return 0
        if(self._run_command(command='docker', args=['volume', 'rm'] + volumes)):
            return 1
        self.initialed = True
        return 0
        
    def construct_network(self):
        if(self._run_command('./netController.sh', ['up'])):
            return 1
        return 0

    def construct_channels(self):
        if(self._run_command('./netController.sh', ['createChannel'])):
            return 1
        return 0
    
    def deploy_chaincodes(self):
        if(self._run_command('./netController.sh', ['deployChaincode'])):
            return 1
        return 0
    
    def deployLedger(self):
        self._run_command('docker', ['ps'])
        if self.stdout.find('orderer') != -1:
            return
        pwd = os.getcwd()
        os.chdir(self.target_path)
        os.chmod('./netController.sh', stat.S_IXOTH | stat.S_IRWXU | stat.S_IXGRP | stat.S_IRGRP | stat.S_IROTH)
        if(os.path.exists(self.target_path)):
            self.construct_network() 
            os.chdir(pwd)
            return
        init_retry = 0
        while(not self.initialed and init_retry < 3): 
            self.init_docker()
            init_retry += 1
        if (not self.initialed):
            raise LedgerBootError('initialize docker failed')
        for chaincode in self.data['chaincodes']:
            os.makedirs(os.path.dirname(chaincode['cc_path']), exist_ok=True)
            self._run_command('cp', ['-r', chaincode['cc_path_origin'], chaincode['cc_path']])
        if(self.construct_network()): 
            os.chdir(pwd)
            raise LedgerBootError('construct network on docker failed:' + self.stderr)
        time.sleep(1)
        if(self.construct_channels()):
            os.chdir(pwd)
            raise LedgerBootError('deploy channels failed:' + self.stderr)
        time.sleep(1)
        if(self.deploy_chaincodes()):
            os.chdir(pwd)
            raise LedgerBootError('deploy chaincodes on channels failed:' + self.stderr)
        os.chdir(pwd)