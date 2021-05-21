class FreePorts(object):
    port_from = 7001
    port_end  = 8000
    port_busy = []
    port_free = list(range(port_from, port_end))
    def __init__(self, portfile = 'freeports.txt'):
        self.portfile = portfile
        with open(self.portfile, 'w+') as f:
            self.port_busy = list(map(lambda p: int(p), f.readlines()))
        self.port_free = list(filter(lambda p: p not in self.port_busy, self.port_free))

    def get_free(self):
        try:
            p = self.port_free.pop()
            self.port_busy.append(p)
            with open(self.portfile, 'a') as f:
                f.write(str(p) + '\n')
            return p
        except:
            return -1
    def free_ports(self, port_list):
        self.port_free.extend(port_list)
        self.port_busy = list(filter(lambda p: p not in self.port_free, self.port_busy))
        with open(self.portfile, 'w') as f:
            f.writelines([str(i) for i in self.port_busy])
