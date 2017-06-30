from django.db import models
from django.utils import timezone
import jsonfield

from . import render_from_template, render_string_or_list, ArrayInputContext
from .base import BaseModel
from .data_channels import DataChannel
from api import get_setting
from api import async
from api.exceptions import ConcurrentModificationError
from api.models import uuidstr
from api.models.task_attempts import TaskAttempt
from api.models import validators


class TaskAlreadyExistsException(Exception):
    pass


class Task(BaseModel):
    """A Task is a Step executed on a particular set of inputs.
    For non-parallel steps, each Run will have one task. For parallel,
    each Run will have one task for each set of inputs.
    """
    uuid = models.CharField(default=uuidstr, editable=False,
                            unique=True, max_length=255)
    interpreter = models.CharField(max_length=1024)
    raw_command = models.TextField()
    command = models.TextField(blank=True)
    environment = jsonfield.JSONField()
    resources = jsonfield.JSONField(blank=True)

    run = models.ForeignKey('Run',
                            related_name='tasks',
                            on_delete=models.CASCADE,
                            null=True, # null for testing only
                            blank=True)
    
    task_attempt = models.OneToOneField('TaskAttempt',
                                        related_name='active_task',
                                        on_delete=models.CASCADE,
                                        null=True,
                                        blank=True)
    data_path = jsonfield.JSONField(
        validators=[validators.validate_data_path],
        blank=True)
    datetime_created = models.DateTimeField(default=timezone.now,
                                            editable=False)
    datetime_finished = models.DateTimeField(null=True, blank=True)
    status_is_finished = models.BooleanField(default=False)
    status_is_failed = models.BooleanField(default=False)
    status_is_killed = models.BooleanField(default=False)
    status_is_running = models.BooleanField(default=False)
    status_is_waiting = models.BooleanField(default=True)

    @property
    def status(self):
        if self.status_is_failed:
            return 'Failed'
        elif self.status_is_finished:
            return 'Finished'
        elif self.status_is_killed:
            return 'Killed'
        elif self.status_is_running:
            return 'Running'
        elif self.status_is_waiting:
            return 'Waiting'
        else:
            return 'Unknown'

    def is_unresponsive(self):
        heartbeat = int(get_setting('TASKRUNNER_HEARTBEAT_INTERVAL_SECONDS'))
        timeout = int(get_setting('TASKRUNNER_HEARTBEAT_TIMEOUT_SECONDS'))
        try:
            last_heartbeat = self.task_attempt.last_heartbeat
        except AttributeError:
            # No TaskAttempt selected
            liast_heartbeat = self.datetime_created
        # Actual interval is expected to be slightly longer than setpoint,
        # depending on settings in TaskRunner. If 2.5 x heartbeat_interval
        # has passed, we have probably missed 2 heartbeats
        return (timezone.now() - last_heartbeat).total_seconds() > timeout

    def fail(self, message, detail=''):
        self.setattrs_and_save_with_retries(
            {'status_is_failed': True,
             'status_is_running': False,
             'status_is_waiting': False})
        self.add_timepoint(message, detail=detail, is_error=True)
        if not self.run.status_is_failed:
            self.run.fail(
                'Task %s failed' % self.uuid,
                detail=detail)

    def finish(self):
        self.setattrs_and_save_with_retries(
            { 'datetime_finished': timezone.now(),
              'status_is_finished': True,
              'status_is_running': False,
              'status_is_waiting': False})
        self.run.add_timepoint('Child Task %s finished successfully' % self.uuid)
        self.run.set_status_is_finished()
        for output in self.outputs.all():
            output.push_data(self.data_path)
        for task_attempt in self.all_task_attempts.all():
            task_attempt.cleanup()

    def kill(self, kill_message):
        self.setattrs_and_save_with_retries({
            'status_is_waiting': False,
            'status_is_running': False,
            'status_is_killed': True
        })
        self.add_timepoint('Task killed', detail=kill_message, is_error=True)
        for task_attempt in self.all_task_attempts.all():
            async.kill_task_attempt(task_attempt.uuid, kill_message)

    @classmethod
    def create_from_input_set(cls, input_set, run):
        if input_set:
            data_path = input_set.data_path
            if run.tasks.filter(data_path=data_path).count() > 0:
                raise TaskAlreadyExistsException
        else:
            # If run has no inputs, we get an empty input_set.
            # Task will go on the root node.
            data_path = []

        task = Task.objects.create(
            run=run,
            raw_command=run.command,
            interpreter=run.interpreter,
            environment=run.template.environment,
            resources=run.template.resources,
            data_path=data_path,
        )
        for input_item in input_set:
            TaskInput.objects.create(
                task=task,
                channel=input_item.channel,
                type=input_item.type,
                mode=input_item.mode,
                data_node = input_item.data_node)
        for run_output in run.outputs.all():
            task_output = TaskOutput.objects.create(
                channel=run_output.channel,
                type=run_output.type,
                task=task,
                mode=run_output.mode,
                source=run_output.source,
                parser=run_output.parser,
                data_node=run_output.data_node.get_or_create_node(data_path))
        task = task.setattrs_and_save_with_retries(
            { 'command': task.render_command() })
        task.add_timepoint('Task %s was created' % task.uuid)
        run.add_timepoint('Child Task %s was created' % task.uuid)
        run.set_running_status()
        return task

    def create_and_activate_attempt(self):
        try:
            task_attempt = TaskAttempt.create_from_task(self)
            self.setattrs_and_save_with_retries({
                'task_attempt': task_attempt,
                'status_is_running': True,
                'status_is_waiting': False})
            self.add_timepoint('Created child TaskAttempt %s' % task_attempt.uuid)
        except ConcurrentModificationError as e:
            task_attempt.add_timepoint(
                'Failed to update task with newly created task_attempt',
                detail=e.message,
                is_error=True)
            task_attempt.fail()
            raise
        task_attempt.add_timepoint('TaskAttempt %s was created' % task_attempt.uuid)
        return task_attempt

    def get_input_context(self):
        context = {}
        for input in self.inputs.all():
            if input.data_node.is_leaf:
                context[input.channel] = input.data_node\
                                              .substitution_value
            else:
                context[input.channel] = ArrayInputContext(
                    input.data_node.substitution_value,
                    input.type
                )
        return context

    def get_output_context(self, input_context):
        context = {}
        for output in self.outputs.all():
            # This returns a value only for Files, where the filename
            # is known beforehand and may be used in the command.
            # For other types, nothing is added to the context.
            if output.source.get('filename'):
                context[output.channel] = render_string_or_list(
                    output.source.get('filename'), input_context)
        return context
    
    def get_full_context(self):
        context = self.get_input_context()
        context.update(self.get_output_context(context))
        return context

    def render_command(self):
        return render_from_template(
            self.raw_command,
            self.get_full_context())

    def get_output(self, channel):
        return self.outputs.get(channel=channel)

    def add_timepoint(self, message, detail='', is_error=False):
        timepoint = TaskTimepoint.objects.create(
            message=message, task=self, detail=detail, is_error=is_error)


class TaskInput(DataChannel):

    task = models.ForeignKey('Task',
                             related_name='inputs',
                             on_delete=models.CASCADE)
    mode = models.CharField(max_length=255)


class TaskOutput(DataChannel):

    task = models.ForeignKey('Task',
                             related_name='outputs',
                             on_delete=models.CASCADE)
    mode = models.CharField(max_length=255)
    source = jsonfield.JSONField(blank=True)
    parser = jsonfield.JSONField(
	validators=[validators.OutputParserValidator.validate_output_parser],
        blank=True)

    def push_data(self, data_path):
        # Copy data from the TaskAttemptOutput to the TaskOutput
        # From there, it is already connected to downstream runs.
        attempt_output = self.task.task_attempt.get_output(self.channel)
        attempt_output.data_node.clone(seed=self.data_node)

        # To trigger new runs we have to push on the root node,
        # but the TaskOutput's data tree may be just a subtree.
        # So we get the root from the run_output.
        run_output = self.task.run.get_output(self.channel)
        data_root = run_output.data_node
        for input in data_root.downstream_run_inputs.all():
            input.run.push(input.channel, data_path)


class TaskTimepoint(BaseModel):
    task = models.ForeignKey(
        'Task',
        related_name='timepoints',
        on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now,
                                     editable=False)
    message = models.CharField(max_length=255)
    detail = models.TextField(blank=True)
    is_error = models.BooleanField(default=False)
