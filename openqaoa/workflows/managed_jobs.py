#   Copyright 2022 Entropica Labs
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import os
import json
# from braket.jobs import save_job_result

from openqaoa.devices import DeviceAWS
from openqaoa.workflows.optimizer import Optimizer, QAOA, RQAOA
from openqaoa.problems.problem import QUBO

class Aws_job(Optimizer):
    """
    This class is meant to be used *only* within the framework of AWS managed hybrid jobs.
    """

    def __init__(self, algorithm: str = 'qaoa'):
        """
        Initialize the QAOA class.

        Parameters
        ----------
            device: `DeviceBase`
                Device to be used by the optimizer. Default is using the local 'vectorized' simulator.
        """
        # the input data directory opt/braket/input/data
        self.input_dir = os.environ["AMZN_BRAKET_INPUT_DIR"]
        # the output directory opt/braket/model to write ob results to
        self.results_dir = os.environ["AMZN_BRAKET_JOB_RESULTS_DIR"]
        # the name of the job
        self.job_name = os.environ["AMZN_BRAKET_JOB_NAME"]
        # the checkpoint directory
        self.checkpoint_dir = os.environ["AMZN_BRAKET_CHECKPOINT_DIR"]
        # the hyperparameter
        self.hyperparameter_file_name = os.environ["AMZN_BRAKET_HP_FILE"]
        # the device ARN (AWS Resource Number)
        self.device_arn = os.environ["AMZN_BRAKET_DEVICE_ARN"]
        # the output S3 bucket, as specified in the CreateJob request’s OutputDataConfig
        self.out_s3_bucket = os.environ["AMZN_BRAKET_OUT_S3_BUCKET"]
        # the entry point as specified in the CreateJob request’s ScriptModeConfig
        self.script_entry_point = os.environ["AMZN_BRAKET_SCRIPT_ENTRY_POINT"]
        # the compression type as specified in the CreateJob request’s ScriptModeConfig
        self.compression_type = os.environ["AMZN_BRAKET_SCRIPT_COMPRESSION_TYPE"]
        # the S3 location of the user’s script as specified in the CreateJob request’s ScriptModeConfig
        self.script_sr_uri = os.environ["AMZN_BRAKET_SCRIPT_S3_URI"]
        # the S3 location where the SDK would store the task results by default for the job
        self.task_results_se_uri = os.environ["AMZN_BRAKET_TASK_RESULTS_S3_URI"]
        # the S3 location where the job results would be stored, as specified in CreateJob request’s OutputDataConfig
        self.results_s3_path = os.environ["AMZN_BRAKET_JOB_RESULTS_S3_PATH"]
        # the string that should be passed to CreateQuantumTask’s jobToken parameter for quantum tasks created in the job container
        self.job_token = os.environ["AMZN_BRAKET_JOB_TOKEN"]

        self.device = DeviceAWS(device_name=self.device_arn, 
                                folder_name=self.results_dir,
                                s3_bucket_name=self.out_s3_bucket)
        self.algorithm = algorithm.lower()
        self.completed = False

    def load_hyperparams(self):
        
        with open(f"{self.input_dir}/hyperparameters/{self.hyperparameter_file_name}", "r") as f:
            hyperparams = json.load(f)
        
        self.hyperparams = hyperparams
        
        

    def extract_qubo(self):
               
        ### Set up the QUBO problem ###
        self.qubo = QUBO(terms=self.hyperparams['qubo']['terms'],
                        weights=self.hyperparams['qubo']['weights'],
                        n=self.hyperparams['qubo']['n'],
                        constant=self.hyperparams['qubo']['constant'])
        

    def aws_jobs_load_workflow(self):
        """
        Given a input directory and a file name loads the json representing the QAOA workflow and returns a 
        valid OpenQAOA workflow
        """

        if 'qaoa' == self.algorithm.lower():
            workflow = QAOA()    
        elif 'rqaoa' == self.algorithm.lower():
            workflow = RQAOA()
            workflow.set_rqaoa_parameters(**self.hyperparams['rqaoa_parameters'])
        else:
            raise ValueError(f'Specified algorithm {self.algorithm} is not supported. Please choose between [QAOA, RQAOA]')
       
        workflow.set_circuit_properties(**self.hyperparams['circuit_properties'])
        workflow.set_classical_optimizer(**self.hyperparams['classical_optimizer'])
        workflow.set_backend_properties(**self.hyperparams['backend_properties'])
        
        # Set the braket device
        workflow.set_device(self.device)

        self.workflow = workflow
    

    def set_up(self):
        """
        The role of this function is to unpack all the raw data incoming from the aws job
        and create the desired workflow
        """

        self.extract_qubo()
        self.aws_jobs_load_workflow()
        self.set_device(self.device)


    def run_workflow(self):
        
        # Run the Workflow hybrid loop
        self.workflow.compile(self.qubo)
        try:
            self.workflow.optimize()
            self.completed = True
            print("Job completed!!!!!")
        except Exception as e:
            print('An Exception has occured when to run the workflow: {}'.format(e))
            return False
        
        






        



