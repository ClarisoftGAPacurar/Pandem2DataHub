from abc import ABC, abstractmethod, ABCMeta
import pykka
import os
import time
import threading
from datetime import datetime, timedelta

class Worker(pykka.ThreadingActor):

    __metaclass__ = ABCMeta  

    class Repeat:
        def __init__(self, tdelta, start=None, end=None):
            self.tdelta = tdelta
            self.start = start
            self.end = end
        
        def next_execution(self, last_excec):
            return last_excec + self.tdelta

    def __init__ (self, name, orchestrator_ref, settings):
        super().__init__()
        self.name = name
        self.settings = settings
        self._orchestrator_proxy = orchestrator_ref.proxy()
        self._self_proxy = self.actor_ref.proxy()
        self._actions = []
        
    
    def on_start(self):
        self.heartbeat_repeat = Worker.Repeat(timedelta(seconds=20))
        self.register_action(self.heartbeat_repeat, self.send_heartbeat) #if action function has parameters use lambda: self.send_heartbeat(self.xyz)
        threading.Thread(target=self.actor_loop).start()

    def send_heartbeat(self):
        self._orchestrator_proxy.get_heartbeat(self.name)

    @abstractmethod
    def actor_loop(self):
        pass


    def pandem_path(self, *args):
        return os.path.join(os.getenv('PANDEM_HOME'), *args)

    def register_action(self, repeat, action, last_exec=None, id_source=None):
        self._actions.append({'repeat': repeat, 'func': action, 'last_exec': last_exec, 'id_source':id_source})
        







    
  
