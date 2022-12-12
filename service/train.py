import sys,os
from service.run_patchcore import patch_core,dataset,run,sampler
from service.config import *




class Train(object):

    def __init__(self, line_id):
        self.line_id = line_id
        self.model_path =  os.path.join(MODELS_FOLDER, str(line_id))
        if not os.path.isdir(self.model_path ):
            os.mkdir(self.model_path )
        self.defects_path = os.path.join(DEFECTS_FOLDER, str(line_id))
        if not os.path.isdir(self.defects_path ):
            os.mkdir(self.defects_path )

        self.data_path = os.path.join(DATA_FOLDER, str(line_id))


    def train(self):
        methods = {}
        methods["get_sampler"] = sampler()
        methods["get_dataloaders"] = dataset(data_path=DATA_FOLDER, line_id=str(self.line_id))
        input_shape = methods["get_dataloaders"][0]["training"].dataset.imagesize
        methods["get_patchcore"]= patch_core(sampler = methods["get_sampler"], input_shape=input_shape)        
        run(methods, self.model_path , self.defects_path)
        return True




        



        


    



