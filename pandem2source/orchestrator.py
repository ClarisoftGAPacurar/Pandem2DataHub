import pykka
from . import storage
from . import acquisition_url
from . import acquisition_git
from . import acquisition_git_local
from . import script_executor
from . import pipeline
from . import formatreader
from . import dfreader
from . import standardizer
from . import variables
import datetime
import os
import pandas as pd
from itertools import chain

class Orchestration(pykka.ThreadingActor):
    
    def __init__(self, settings, start_acquisition = True):
        super(Orchestration, self).__init__()
        self.settings = settings
        self.current_actors = dict()
        self.start_acquisition = start_acquisition
        
   
    def on_start(self):      
        # Launching the storage actor which can be used by any actor
        storage_ref = storage.Storage.start('storage', self.actor_ref, self.settings)
        self.current_actors['storage'] = {'ref': storage_ref}

        # Launching passive actors
        # launch dataframe reader acor
        dfreader_ref = dfreader.DataframeReader.start('dfreader', self.actor_ref, storage_ref, self.settings)
        self.current_actors['dfreader'] = {'ref': dfreader_ref}
        
        # launch format reader actor
        ftreader_ref = formatreader.FormatReader.start('ftreader', self.actor_ref, storage_ref, self.settings)
        self.current_actors['ftreader'] = {'ref': ftreader_ref}
        
        # launch pipeline actor
        pipeline_ref = pipeline.Pipeline.start('pipeline', self.actor_ref, self.settings)
        self.current_actors['pipeline'] = {'ref': pipeline_ref}
        
        # launch script executor reader
        script_executor_ref = script_executor.ScriptExecutor.start('script_executor', self.actor_ref, self.settings)
        self.current_actors['script_executor'] = {'ref': script_executor_ref}
        
        
        # launch standardizer actor
        standardizer_ref = standardizer.Standardizer.start('standardizer', self.actor_ref, self.settings)
        self.current_actors['standardizer'] = {'ref': standardizer_ref}
        
        # launch variables actor
        variables_ref = variables.Variables.start('variables', self.actor_ref, self.settings)
        self.current_actors['variables'] = {'ref': variables_ref}
       
        # Launching acquisition actors (active actors)
        # List source definition files within 'source-definitions' through storage actor to get 
        source_files = storage_ref.proxy().list_files('source-definitions').get()
        # read json dls files into dicts
        dls_dicts = [storage_ref.proxy().read_files(file_name['path']).get() for file_name in source_files]
        sources_labels = set([dls['acquisition']['channel']['name'] for dls in dls_dicts])
        
        if self.start_acquisition:
            for label in sources_labels:
                if label == "url":
                    acquisition_ref = acquisition_url.AcquisitionURL.start(name = 'acquisition_'+label, orchestrator_ref = self.actor_ref, settings = self.settings)
                elif label == "git":
                    acquisition_ref = acquisition_git.AcquisitionGIT.start(name = 'acquisition_'+label, orchestrator_ref = self.actor_ref, settings = self.settings)
                elif label == "git-local":
                    acquisition_ref = acquisition_git_local.AcquisitionGITLocal.start(name = 'acquisition_'+label, orchestrator_ref = self.actor_ref, settings = self.settings)
                else:
                  raise NotImplementedError(f"The acquisition channel {label} has not been implemented")

                acquisition_proxy = acquisition_ref.proxy()
                dls_label = [dls for dls in dls_dicts if dls['acquisition']['channel']['name'] == label]
                for dls in dls_label:
                    acquisition_proxy.add_datasource(dls)
                self.current_actors['acquisition_'+label] = {'ref': acquisition_ref, 'sources': dls_label} 
        
        
    def get_heartbeat(self, actor_name):
        now = datetime.datetime.now()
        self.current_actors[actor_name]['heartbeat'] = now
        #print(f'heartbeat from {actor_name} at: {now}')
        
    def get_actor(self, actor_name):
        return self.current_actors[actor_name]['ref']



    def actors_df(self):
      map = self.current_actors
      df = pd.DataFrame(data = {
        "actor": map.keys(), 
        "last_seen_seconds": [((datetime.datetime.now() - it["heartbeat"]).total_seconds() if "heartbeat" in it else pd.NA)  for it in map.values()],
        "heartbeat": [(it["heartbeat"] if "heartbeat" in it else pd.NA)  for it in map.values()]
      })
      return df 
    



    
