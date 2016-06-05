from django.core.exceptions import ValidationError

from analysis.exceptions import *
from analysis.models.base import AnalysisAppInstanceModel, AnalysisAppImmutableModel
from universalmodels import fields


"""
This module defines Workflow and its children.
A Workflow is a template of an analysis to run, where
some inputs may be specified at runtime.
"""


class AbstractWorkflow(AnalysisAppImmutableModel):
    """An AbstractWorkflow is either a step or a collection of steps.
    Workflows are ImmutableModels in order to prevent clutter. If the same workflow 
    or step is uploaded multiple times, duplicate objects will not be created.
    """

    NAME_FIELD = 'name'
    
    name = fields.CharField(max_length=255)

    def is_step(self):
        return self.downcast().is_step()


class Workflow(AbstractWorkflow):
    """A collection of steps or workflows
    """

    steps = fields.ManyToManyField('AbstractWorkflow', related_name='parent_workflow')
    inputs = fields.ManyToManyField('WorkflowInput')
    outputs = fields.ManyToManyField('WorkflowOutput')

    def after_create(self):
        self._validate_workflow()

    def _validate_workflow(self):
        """Make sure all channel destinations have exactly one source
        """

        source_counts = {}
        for input in self.inputs.all():
            self._increment_sources_count(source_counts, input.channel)
        for step in self.steps.all():
            step = step.downcast()
            for output in step.outputs.all():
                self._increment_sources_count(source_counts, output.channel)

        for channel, count in source_counts.iteritems():
            if count > 1:
                raise ValidationError('The workflow %s@%s is invalid. It has more than one source for channel "%s". Check workflow inputs and step outputs.' % (
                    self.name,
                    self._id,
                    channel
                ))

        destinations = []
        for output in self.outputs.all():
            destinations.append(output.channel)
        for step in self.steps.all():
            step = step.downcast()
            for input in step.inputs.all():
                destinations.append(input.channel)

        sources = source_counts.keys()
        for destination in destinations:
            if not destination in sources:
                raise ValidationError('The workflow %s@%s is invalid. The channel "%s" has no source.' % (
                    self.name,
                    self._id,
                    destination
                ))

    def _increment_sources_count(self, sources, channel):
        sources.setdefault(channel, 0)
        sources[channel] += 1

    def is_step(self):
        return False

class Step(AbstractWorkflow):
    """Steps are smaller units of processing within a Workflow. A Step can give rise to a single process,
    or it may iterate over an array to produce many parallel processing tasks.
    """

    command = fields.CharField(max_length=255)
    environment = fields.ForeignKey('RequestedEnvironment')
    resources = fields.ForeignKey('RequestedResourceSet')
    inputs = fields.ManyToManyField('StepInput')
    outputs = fields.ManyToManyField('StepOutput')

    def is_step(self):
        return True

    def get_output(self, channel):
        outputs = self.outputs.filter(channel=channel)
        assert outputs.count() == 1
        return outputs.first()

class RequestedEnvironment(AnalysisAppImmutableModel):

    pass


class RequestedDockerEnvironment(RequestedEnvironment):

    docker_image = fields.CharField(max_length=255)


class RequestedResourceSet(AnalysisAppImmutableModel):

    memory = fields.CharField(max_length=255)
    disk_space = fields.CharField(max_length=255)
    cores = fields.CharField(max_length=255)


class AbstractInput(AnalysisAppImmutableModel):

    hint = fields.CharField(max_length=255, null=True)
    type = fields.CharField(
        max_length=255,
        choices=(
            ('file', 'File'),
            # ('file_array', 'File Array'),
            # ('boolean', 'Boolean'),
            # ('boolean_array', 'Boolean Array'),
            # ('string', 'String'),
            # ('string_array', 'String Array'),
            # ('integer', 'Integer'),
            # ('integer_array', 'Integer Array'),
            # ('float', 'Float'),
            # ('float_array', 'Float Array'),
            # ('json', 'JSON'),
            # ('json_array', 'JSON Array')
        )
    )
    channel = fields.CharField(max_length=255)

    class Meta:
        abstract = True

        
class WorkflowInput(AbstractInput):

    pass


class StepInput(AbstractInput):

    pass


class AbstractOutput(AnalysisAppImmutableModel):

    channel = fields.CharField(max_length=255)
    type = fields.CharField(
        max_length=255,
        choices=(
            ('file', 'File'),
            # ('file_array', 'File Array'),
            # ('boolean', 'Boolean'),
            # ('boolean_array', 'Boolean Array'),
            # ('string', 'String'),
            # ('string_array', 'String Array'),
            # ('integer', 'Integer'),
            # ('integer_array', 'Integer Array'),
            # ('float', 'Float'),
            # ('float_array', 'Float Array'),
            # ('json', 'JSON'),
            # ('json_array', 'JSON Array')
        )
    )

    class Meta:
        abstract = True


class WorkflowOutput(AbstractOutput):

    pass


class StepOutput(AbstractOutput):

    filename = fields.CharField(max_length=255)
