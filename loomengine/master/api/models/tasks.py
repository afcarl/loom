from django.db import models
# from django.dispatch import receiver
from django.utils import timezone
import os

from api.models import uuidstr
from .base import BaseModel, render_from_template
from api.models.data_objects import DataObject
# from api.models.workflows import Step, RequestedResourceSet
from api import get_setting
from api.task_manager.factory import TaskManagerFactory

TASK_STATUSES = [
    ('STARTING', 'Starting'),
    ('RUNNING', 'Running'),
    ('FINISHED', 'Finished'),
    ('FAILED', 'Failed'),
]

TASK_DETAILED_STATUSES = {
    'STARTING': 'Starting',
    'RUNNING_PROVISIONING_HOST': 'Provisioning host',
    'RUNNING_LAUNCHING_MONITOR': 'Launching monitor process on worker',
    'RUNNING_INITIALIZING_MONITOR': 'Initializing monitor process on worker',
    'RUNNING_COPYING_INPUTS': 'Copying input files to runtime environment',
    'RUNNING_CREATING_RUN_SCRIPT': 'Creating run script',
    'RUNNING_FETCHING_IMAGE': 'Fetching runtime environment image',
    'RUNNING_CREATING_CONTAINER': 'Creating runtime environment container',
    'RUNNING_STARTING_ANALYSIS': 'Starting analysis',
    'RUNNING_EXECUTING_ANALYSIS': 'Running analysis',
    'RUNNING_SAVING_OUTPUTS': 'Saving outputs',
    'FINISHED': 'Finished',
    'FAILED': 'Failed',
}


class Task(BaseModel):

    """A Task is a Step executed on a particular set of inputs.
    For non-parallel steps, each StepRun will have one task. For parallel,
    each StepRun will have one task for each set of inputs.
    """

    uuid = models.CharField(default=uuidstr, editable=False,
                            unique=True, max_length=255)
    datetime_created = models.DateTimeField(default=timezone.now,
                                            editable=False)
    datetime_finished = models.DateTimeField(null=True)
    interpreter = models.CharField(max_length=255, default='/bin/bash')
    command = models.TextField()
    rendered_command = models.TextField()

    step_run = models.ForeignKey('StepRun',
                                 related_name='tasks',
                                 on_delete=models.CASCADE,
                                 null=True) # null for testing only

    status = models.CharField(
        max_length=255,
        default='STARTING',
        choices=TASK_STATUSES,
    )
    status_detail = models.CharField(
        max_length=255,
        default=TASK_DETAILED_STATUSES['STARTING'])
    attempt_number = models.IntegerField(default=1)

#    @property
#    def errors(self):
#        if self.task_attempts.count() == 0:
#            return TaskAttemptError.objects.none()
#        return self.task_attempts.first().errors

    @classmethod
    def create_from_input_set(cls, input_set, step_run):
        task = Task.objects.create(
            step_run=step_run,
            command=step_run.command,
        )
        task.rendered_command = task.render_command
        task.save()

        for input in input_set:
            TaskInput.objects.create(
                task=task,
                channel=input.channel,
                type=input.type,
                data_object = input.data_object)
        for step_run_output in step_run.outputs.all():
            TaskOutput.objects.create(
                channel = step_run_output.channel,
                type=step_run_output.type,
                task=task)
        TaskResourceSet.objects.create(
            task=task,
            memory=step_run.template.resources.memory,
            disk_size=step_run.template.resources.disk_size,
            cores=step_run.template.resources.cores
        )
        TaskEnvironment.objects.create(
            task=task,
            docker_image = step_run.template.environment.docker_image,
        )
        return task

    def run(self):
        task_manager = TaskManagerFactory.get_task_manager()
        task_manager.run(self)

    def create_attempt(self):
        attempt = TaskAttempt.objects.create(task=self)
        attempt.initialize()
        return attempt

    def get_input_context(self):
        context = {}
        for input in self.inputs.all():
            context[input.channel] = input.data_object\
                                            .get_substitution_value()
        return context

    def get_output_context(self):
        context = {}
        for output in self.outputs.all():
            # This returns a value only for Files, where the filename
            # is known beforehand and may be used in the command.
            # For other types, nothing is added to the context.
            if output.source.filename:
                context[output.channel] = output.source.filename
        return context

    def get_full_context(self):
        context = self.get_input_context()
        context.update(self.get_output_context())
        return context

    def render_command(self):
        return render_from_template(
            self.command,
            self.get_full_context())

    def update_status(self):
        self.step_run.update_status()


class TaskInput(BaseModel):

    task = models.ForeignKey('Task',
                             related_name='inputs',
                             on_delete=models.CASCADE)
    data_object = models.ForeignKey('DataObject', on_delete=models.PROTECT)
    channel = models.CharField(max_length=255)
    type = models.CharField(max_length = 255,
                            choices=DataObject.TYPE_CHOICES)


class TaskOutput(BaseModel):

    task = models.ForeignKey('Task',
                             related_name='outputs',
                             on_delete=models.CASCADE)
    data_object = models.ForeignKey('DataObject',
                                    null=True,
                                    on_delete=models.PROTECT)
    channel = models.CharField(max_length=255)
    type = models.CharField(max_length = 255,
                            choices=DataObject.TYPE_CHOICES)


class TaskOutputSource(BaseModel):

    task_output = models.OneToOneField(
        TaskOutput,
        related_name='source',
        on_delete=models.CASCADE)
    filename = models.CharField(max_length=255)
    stream = models.CharField(max_length=255,
                              choices=(('stdout', 'stdout'),
                                       ('sterr','stderr')))


class TaskResourceSet(BaseModel):
    task = models.OneToOneField('Task',
                                on_delete=models.CASCADE,
                                related_name='resources')
    memory = models.CharField(max_length=255, null=True)
    disk_size = models.CharField(max_length=255, null=True)
    cores = models.CharField(max_length=255, null=True)


class TaskEnvironment(BaseModel):

    task = models.OneToOneField(
        'Task',
        on_delete=models.CASCADE,
        related_name='environment')
    docker_image = models.CharField(max_length=255)


class TaskAttempt(BaseModel):

    uuid = models.CharField(default=uuidstr, editable=False,
                            unique=True, max_length=255)
    datetime_created = models.DateTimeField(default=timezone.now,
                                            editable=False)
    datetime_finished = models.DateTimeField(null=True)
    task = models.ForeignKey('Task',
                             related_name='task_attempts',
                             on_delete=models.CASCADE)
    task_as_accepted_attempt = models.OneToOneField(
        'Task',
        related_name='accepted_task_attempt',
        on_delete=models.CASCADE,
        null=True
    )
    # container_id = models.CharField(max_length=255, null=True)
    last_heartbeat = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=255,
        default='STARTING',
        choices=TASK_STATUSES,
    )
    status_detail = models.CharField(
        max_length=255,
        default=TASK_DETAILED_STATUSES['STARTING'])

    @property
    def name(self):
        return self.task.name

    @property
    def interpreter(self):
        return self.task.interpreter

    @property
    def rendered_command(self):
        return self.task.rendered_command

    @property
    def inputs(self):
        return self.task.inputs

    @property
    def resources(self):
        return self.task.resources

    @property
    def environment(self):
        return self.task.environment

    def add_error(self, message, detail):
        error = TaskAttemptError.objects.create(
            message=message, detail=detail, task_attempt=self)
        error.save()

    @classmethod
    def create_from_task(cls, task):
        task_attempt = cls.objects.create(task=task)
        task_attempt.initialize()
        return task_attempt

    def initialize(self):
        if self.inputs.count() == 0:
            self._initialize_inputs()

        if self.outputs.count() == 0:
            self._initialize_outputs()

    def _initialize_outputs(self):
        for output in self.task.outputs.all():
            TaskAttemptOutput.objects.create(
                task_attempt=self,
                task_output=output)

    def get_working_dir(self):
        return os.path.join(get_setting('FILE_ROOT_FOR_WORKER'),
                            'runtime_volumes',
                            self.id,
                            'work')

    def get_log_dir(self):
        return os.path.join(get_setting('FILE_ROOT_FOR_WORKER'),
                            'runtime_volumes',
                            self.id,
                            'logs')

    def get_worker_log_file(self):
        return os.path.join(self.get_log_dir(), 'worker.log')

    def get_stdout_log_file(self):
        return os.path.join(self.get_log_dir(), 'stdout.log')

    def get_stderr_log_file(self):
        return os.path.join(self.get_log_dir(), 'stderr.log')

#    def get_provenance_data(self, files=None, tasks=None, edges=None):
#        if files is None:
#            files = set()
#        if tasks is None:
#            tasks = set()
#        if edges is None:
#            edges = set()

#        tasks.add(self)

#        for input in self.task.inputs.all():
#            data = input.data_object
#            if data.type == 'file':
#                files.add(data)
#                edges.add((data.id.hex, self.id.hex))
#                data.get_provenance_data(files, tasks, edges)
#            else:
                # TODO - nonfile data types
#                pass

#        return files, tasks, edges

#    def push_outputs(self):
#        for output in self.outputs.all():
#            output.push()
#        self.task.step_run.get_run_request().create_ready_tasks()

#    def _post_save(self):
#        if self.status == 'Finished':
#            self.push_outputs()
#        self.task.update_status()

#@receiver(models.signals.post_save, sender=TaskAttempt)
#def _post_save_task_attempt_signal_receiver(sender, instance, **kwargs):
#    instance._post_save()


class TaskAttemptOutput(BaseModel):
    
    # All info here is saved in the TaskOutput,
    # except for the data_object. If multiple
    # attempts are run, each may have a different
    # data_object.

    task_attempt = models.ForeignKey(
        'TaskAttempt',
        related_name='outputs',
        on_delete=models.CASCADE)
    data_object = models.OneToOneField(
        'DataObject',
        null=True,
        related_name='task_attempt_output',
        on_delete=models.PROTECT)
    task_output = models.ForeignKey(
        'TaskOutput',
        related_name='task_attempt_outputs',
        on_delete=models.PROTECT)

    @property
    def type(self):
        return self.task_output.type

    @property
    def channel(self):
        return self.task_output.channel

    @property
    def source(self):
        return self.task_output.source


class TaskAttemptLogFile(BaseModel):

    task_attempt = models.ForeignKey(
        'TaskAttempt',
        related_name='log_files',
        on_delete=models.CASCADE)
    log_name = models.CharField(max_length=255)
    file = models.OneToOneField(
        'DataObject',
        null=True,
        related_name='task_attempt_log_file',
        on_delete=models.PROTECT)


class TaskAttemptError(BaseModel):

    task_attempt = models.ForeignKey(
        'TaskAttempt',
        related_name='errors',
        on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    detail = models.TextField(null=True, blank=True)
