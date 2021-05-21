import os

import os, json
class LedgerStore(object):
    
    def __init__(self, store = 'ledgerstore.json'):
        self.ledgers = {}
        self.store = store
        self._from_file()

    def _from_file(self):
        if not os.path.exists(self.store):
            with open(self.store, 'w') as jsonf:
               json.dump(self.ledgers, jsonf) 
        else:
            with open(self.store, 'r') as jsonf:
                self.ledgers = json.load(jsonf)
            for item in self.ledgers:
                self.ledgers[item]['status'] = 'suspend'

    def _to_file(self):
        with open(self.store, 'w') as jsonf:
            json.dump(self.ledgers, jsonf)

    def __exit__(self):
        self._to_file()
    
    def __getitem__(self, project): 
        if project in self.ledgers:
            return self.ledgers[project]
        else:
            return None
    
    def append(self, project_info, status = 'running'):
        self.ledgers[project_info['project_name']] \
            = project_info
        self.ledgers[project_info['project_name']]['status'] = 'running'
        self._to_file()
    
    def exist(self, project):
        return project in self.ledgers

    def remove(self, project):
        if project in self.ledgers:
            self.ledgers.pop(project)
        self._to_file()
    
    def items(self):
        return self.ledgers

