# glue workflow helper functions
# from '../journal_stack.py' import generateResourceName

# def _create_glue_workflow(self, workflow_name, description=None, max_concurrent_runs=2):
#     name = generateResourceName(f"{workflow_name}-glue-workflow")
#     if not description:
#         description = f"Glue workflow for {workflow_name}"
#     default_run_properties = {}
#     return glue.CfnWorkflow(
#             self, name,
#             default_run_properties=default_run_properties,
#             description=description,
#             max_concurrent_runs=max_concurrent_runs,
#             name=name
#     )

def _create_glue_job(self, job_name, script_name, connections=None, max_concurrent_runs=2):
    name = generateResourceName(f"{job_name}-glue-job")
    glue_job = alpha_glue.Job(
        self,
        name,
        job_name=name,
        executable=alpha_glue.JobExecutable.python_etl(
            glue_version=alpha_glue.GlueVersion.V3_0,
            python_version=alpha_glue.PythonVersion.THREE,
            script=alpha_glue.Code.from_asset(
                f"../../../data-pipelines/{data_source}Pipeline/glue/{script_name}"
            ),
        ),
        max_concurrent_runs=max_concurrent_runs,
        continuous_logging=alpha_glue.ContinuousLoggingProps(enabled=True),
        connections=connections
    )
    # glue_job.role.add_managed_policy(self.s3_managed_policy)
    # if connections:
    # glue_job.role.add_managed_policy(self.secrets_managed_policy)
    # glue_job.role(add_managed_policy(self.rds_managed_policy)
    # glue_alarm = self._create_alarm(job_name, glue_job.metric_failure())
    return glue_job
