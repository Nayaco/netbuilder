import subprocess, os, sys, stat, time, shutil

import weaver.createConfigurations as createConfigurations
import weaver.createScript as createScript

class LedgerBootError(RuntimeError):
    def __init__(self, msg):
        self.msg = msg

class ShellColors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class LedgerController(object):
    target_path = './'
    environment = {}
    runtime_env = os.environ.copy() 
    stdout = ''
    stderr = ''
    logfile = os.getcwd() + '/log.txt'
    initialed = False

    data = {}
    def __init__(self, target_path=None, env={}, logfile=os.getcwd() + '/log.txt', data={}): 
        self.target_path = data['script_pwd'] + '/' + data['target_path'] if target_path is None else target_path
        self.environment = env
        self.runtime_env = {**self.runtime_env, **self.environment}
        self.logfile = logfile
        self.data = data

    def _set_env(self, env_key, env_val=''): 
        self.environment[env_key] = env_val
        self.runtime_env[env_key] = env_val
    
    def _run_command(self, command='pwd', args=[], quiet=False):
        process_command = [command] + args
        process = subprocess.Popen(
                process_command,
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                env=self.runtime_env)
        _stdout = ''
        if not quiet:
            with open(self.logfile, 'a+') as log:
                for line in process.stdout:
                    sys.stdout.write(line.decode('utf-8'))
                    _stdout = _stdout + line.decode('utf-8')
                    log.write(line.decode('utf-8'))
                    log.flush()
        _stdout_, _stderr = process.communicate()
        self.stdout = _stdout
        return process.returncode

    def _init_docker(self):
        containers = [self.data['orderer']['orderer_name'].lower() + '.' + self.data['orderer']['orderer_domain']]
        for peer in self.data['peerorgs']:
            containers = containers + [
                'peer' + str(i) + '.' + peer['peer_name'].lower() + '.' + peer['peer_domain']
                for i in range(0, peer['peer_nodes'])]
        self._run_command(command='docker', args=['stop'] + containers, quiet=True)
        self._run_command(command='docker', args=['rm'] + containers, quiet=False)
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
        
    def _bringup_network(self):
        if(self._run_command('./netController.sh', ['up'])):
            return 1
        return 0
    
    def _shutdown_network(self):
        if(self._run_command('./netController.sh', ['down'])):
            return 1
        return 0

    def _suspend_network(self):
        if(self._run_command('./netController.sh', ['suspend'])):
            return 1
        return 0

    def _wakeup_network(self):
        if(self._run_command('./netController.sh', ['wakeup'])):
            return 1
        return 0

    def _construct_channels(self):
        if(self._run_command('./netController.sh', ['createChannel'])):
            return 1
        return 0
    
    def _deploy_chaincodes(self):
        if(self._run_command('./netController.sh', ['deployChaincode'])):
            return 1
        return 0
    
    def deployLedger(self):
        pwd = os.getcwd()
        
        if(os.path.exists(self.target_path)):
            print('\n' + ShellColors.BLUE + '[Ledger Controller]' + ShellColors.ENDC + ':Starting Container' + '\n')
            os.chdir(self.target_path)
            self.initialed = True
            self._bringup_network()
            os.chdir(pwd)
            return
            
        createConfigurations.gen_core_config_conf(self.target_path, self.data)
        createConfigurations.gen_cryptogen_conf(self.target_path, self.data)
        createConfigurations.gen_dockers_conf(self.target_path, self.data)
        createConfigurations.gen_fabric_ca_server_conf(self.target_path, self.data)

        createScript.create_registerEnroll(self.target_path, self.data)
        createScript.create_envVars(self.target_path, self.data)
        createScript.create_createChannel(self.target_path, self.data)
        createScript.create_DeployChaincode(self.target_path, self.data)
        createScript.create_netController(self.target_path, self.data)
        
        os.chdir(self.target_path)
        os.chmod('./netController.sh', stat.S_IXOTH | stat.S_IRWXU | stat.S_IXGRP | stat.S_IRGRP | stat.S_IROTH)

        self.initialed = True
        if (not self.initialed):
            raise LedgerBootError('initialize docker failed')
        for chaincode in self.data['chaincodes']:
            os.makedirs(os.path.dirname(chaincode['cc_path']), exist_ok=True)
            self._run_command('cp', ['-r', chaincode['cc_path_origin'], chaincode['cc_path']])
        if(self._bringup_network()): 
            os.chdir(pwd)
            raise LedgerBootError('construct network on docker failed:' + self.stderr)
        time.sleep(1)

        print('\n' + ShellColors.GREEN + '[Ledger Controller]' + ShellColors.ENDC + ':Deploying Channel' + '\n')
        
        if(self._construct_channels()):
            os.chdir(pwd)
            raise LedgerBootError('deploy channels failed:' + self.stderr)
        time.sleep(1)
        if(self._deploy_chaincodes()):
            os.chdir(pwd)
            raise LedgerBootError('deploy chaincodes on channels failed:' + self.stderr)
        os.chdir(pwd)
    def activeLedger(self):
        pwd = os.getcwd()
        if(os.path.exists(self.target_path)):
            print('\n' + ShellColors.BLUE + '[Ledger Controller]' + ShellColors.ENDC + ':Starting Container' + '\n')
            os.chdir(self.target_path)
            self._wakeup_network()
            os.chdir(pwd)
            return 0
        else:
            print('\n' + ShellColors.FAIL + '[Ledger Controller]' + ShellColors.ENDC + ':Starting Container Failed, Ledger Not Exist' + '\n')
            os.chdir(pwd)
            return 1
    def suspendLedger(self):
        pwd = os.getcwd()
        if(os.path.exists(self.target_path)):
            print('\n' + ShellColors.BLUE + '[Ledger Controller]' + ShellColors.ENDC + ':Suspending Container' + '\n')
            os.chdir(self.target_path)
            self._suspend_network()
            os.chdir(pwd)
            return 0
        else:
            print('\n' + ShellColors.FAIL + '[Ledger Controller]' + ShellColors.ENDC + ':Suspending Container Failed, Ledger Not Exist' + '\n')
            os.chdir(pwd)
            return 1
    def shutdownLedger(self):
        pwd = os.getcwd()
        if(os.path.exists(self.target_path)):
            print('\n' + ShellColors.BLUE + '[Ledger Controller]' + ShellColors.ENDC + ':Shutting Down Container' + '\n')
            os.chdir(self.target_path)
            self._shutdown_network()
            os.chdir(pwd)
            return 0
        else:
            print('\n' + ShellColors.FAIL + '[Ledger Controller]' + ShellColors.ENDC + ':Shutting Down Container Failed, Ledger Not Exist' + '\n')
            os.chdir(pwd)
            return 1

    def removeLedger(self):
        if(os.path.exists(self.target_path)):
            shutil.rmtree(self.target_path)
            os.remove(self.logfile)