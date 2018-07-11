from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
import jsonfield
import os

from . import calculate_contents_fingerprint
from .base import BaseModel
from api import get_setting
from api.models import uuidstr
from api.models import validators


"""DataObjects represent units of data generated by workflows.
These can be one of the following types:
- file
- string
- boolean
- integer
- float

Each DataObject has a uuid to serve as a globally unique identifier
for traceability.
"""


class DataObject(BaseModel):

    NAME_FIELD = 'file_resource__filename'
    HASH_FIELD = 'file_resource__md5'
    ID_FIELD = 'uuid'
    TAG_FIELD = 'tags__tag'

    DATA_TYPE_CHOICES = (
        ('boolean', 'Boolean'),
        ('file', 'File'),
        ('float', 'Float'),
        ('integer', 'Integer'),
        ('string', 'String'),
    )

    uuid = models.CharField(default=uuidstr,
                            unique=True, max_length=255)
    type = models.CharField(
        max_length=16,
        choices=DATA_TYPE_CHOICES)
    datetime_created = models.DateTimeField(
        default=timezone.now)
    data = jsonfield.JSONField(blank=True)

    def clean(self):
        validators.DataObjectValidator.validate_model(self)

    @classmethod
    def get_by_value(cls, value, type):
        """ Converts a value into a corresponding  data object.
        For files, this looks up a file DataObject by name, uuid, and/or md5.
        For other types, it creates a new DataObject.
        """
        if type == 'file':
            return cls._get_file_by_value(value)
        else:
            data_object = DataObject(data={
                'value': cls._type_cast(value, type)}, type=type)
            data_object.full_clean()
            data_object.save()
            return data_object

    FALSE_VALUES = [False, 0, '', 'false', 'False', 'FALSE',
                    'f', 'F', 'no', 'No', 'NO', 'n', 'N', '0']

    @classmethod
    def _type_cast(cls, value, type):
        try:
            if type == 'string':
                return str(value)
            if type == 'integer':
                return int(value)
            if type == 'float':
                return float(value)
            if type == 'boolean':
                return not value in cls.FALSE_VALUES
        except ValueError:
            raise ValidationError('"%s" is not a valid %s' % (value, type))

    @classmethod
    def _get_file_by_value(cls, value):
        """Look up a file DataObject by name, uuid, and/or md5.
        """
        # Ignore any FileResource with no DataObject. This is a typical state
        # for a deleted file that has not yet been cleaned up.
        queryset = FileResource.objects.exclude(data_object__isnull=True)
        matches = FileResource.filter_by_name_or_id_or_tag_or_hash(
            value, queryset=queryset)
        if matches.count() == 0:
            raise ValidationError(
                'No file found that matches value "%s"' % value)
        elif matches.count() > 1:
            match_id_list = ['%s@%s' % (match.filename, match.get_uuid())
                             for match in matches]
            match_id_string = ('", "'.join(match_id_list))
            raise ValidationError(
                'Multiple files were found matching value "%s": "%s". '\
                'Use a more precise identifier to select just one file.' % (
                    value, match_id_string))
        return matches.first().data_object

    @property
    def _value_info(self):
        return self.type, self.value

    @property
    def value(self):
        if self.type == 'file':
            return self.file_resource
        else:
            return self.data.get('value')

    @property
    def substitution_value(self):
        if self.type == 'file':
            return self.file_resource.filename
        else:
            return str(self.value)

    @property
    def is_ready(self):
        if self.type == 'file':
            return self.file_resource is not None \
                and self.file_resource.is_ready
        else:
            return self.data and 'value' in self.data.keys()

    @classmethod
    def create_and_initialize_file_resource(cls, **kwargs):
        data_object = cls(type='file')
        data_object.full_clean()
        data_object.save()
        kwargs['data_object'] = data_object
        file_resource = FileResource.initialize(**kwargs)
        file_resource.full_clean()
        file_resource.save()
        return data_object

    @classmethod
    def get_dependencies(cls, uuid, request):

        from .data_nodes import DataNode
        from api.serializers import URLRunSerializer, URLTemplateSerializer

        context = {'request': request}
        # We truncate the dependencies listed if we exceed DEPENDENCY_LIMIT
        DEPENDENCY_LIMIT = 10
        truncated = False
        runs = set()
        templates = set()

        data_object = cls.objects.filter(uuid=uuid).prefetch_related('data_nodes')
        if data_object.count() < 1:
            raise cls.DoesNotExist
        prefetched_root_data_nodes = DataNode.objects.filter(
            tree_id__in=[node.tree_id
                         for node in data_object.first().data_nodes.all()],
            parent=None).\
            prefetch_related('runinput_set__run').\
            prefetch_related('runoutput_set__run').\
            prefetch_related('userinput_set__run').\
            prefetch_related('taskinput_set__task__run').\
            prefetch_related('taskoutput_set__task__run').\
            prefetch_related('taskattemptinput_set__task_attempt__tasks__run').\
            prefetch_related('taskattemptoutput_set__task_attempt__tasks__run').\
            prefetch_related('templateinput_set__template')

        for data_node in prefetched_root_data_nodes:
            for run_input in data_node.runinput_set.all():
                if len(runs)+len(templates) >= DEPENDENCY_LIMIT \
                   and run_input.run not in runs:
                    truncated = True
                    break
                runs.add(run_input.run)
            for run_output in data_node.runoutput_set.all():
                if len(runs)+len(templates) >= DEPENDENCY_LIMIT \
                   and run_output.run not in runs:
                    truncated = True
                    break
                runs.add(run_output.run)
            for user_input in data_node.userinput_set.all():
                if len(runs)+len(templates) >= DEPENDENCY_LIMIT \
                   and user_input.run not in runs:
                    truncated = True
                    break
                runs.add(user_input.run)
            for task_input in data_node.taskinput_set.all():
                if len(runs)+len(templates) >= DEPENDENCY_LIMIT \
                   and task_input.task.run not in runs:
                    truncated = True
                    break
                runs.add(task_input.task.run)
            for task_output in data_node.taskoutput_set.all():
                if len(runs)+len(templates) >= DEPENDENCY_LIMIT \
                   and task_output.task.run not in runs:
                    truncated = True
                    break
                runs.add(task_output.task.run)
            for task_attempt_input in data_node.taskattemptinput_set.all():
                for task in task_attempt_input.task_attempt.tasks.all():
                    if len(runs)+len(templates) >= DEPENDENCY_LIMIT \
                       and task.run not in runs:
                        truncated = True
                        break
                    runs.add(task.run)
            for task_attempt_output in data_node.taskattemptoutput_set.all():
                for task in task_attempt_output.task_attempt.tasks.all():
                    if len(runs)+len(templates) >= DEPENDENCY_LIMIT \
                       and task.run not in runs:
                        truncated = True
                        break
                    runs.add(task.run)
            for template_input in data_node.templateinput_set.all():
                if len(runs)+len(templates) >= DEPENDENCY_LIMIT \
                   and template_input.template not in templates:
                    truncated = True
                    break
                templates.add(template_input.template)
            if truncated == True:
                break

        run_dependencies = []
        for run in runs:
            run_dependencies.append(
                URLRunSerializer(run, context=context).data)

        template_dependencies = []
        for template in templates:
            template_dependencies.append(
                URLTemplateSerializer(template, context=context).data)

        return {'runs': run_dependencies,
                'templates': template_dependencies,
                'truncated': truncated}

    def has_dependencies(self):
        dependencies = self.get_dependencies(self.uuid, {})
        return any(dependencies.values())

    def delete(self):
        # Sometimes detached DataNodes can be accidentially created, for example
        # if there is an error when importing the Template after an input
        # DataNode was already created. As a precaution we remove any extra
        # DataNodes after verifying that none are in use.
        if not self.has_dependencies():
            self._cleanup_data_nodes()
        super(DataObject, self).delete()

    def _cleanup_data_nodes(self):
        for node in self.data_nodes.all():
            node.delete()

            
    def get_fingerprintable_contents(self):
        if self.type == 'file':
            return {
                'type': 'file',
                'value': self.file_resource.get_fingerprintable_contents()}
        else:
            return {
                'type': self.type,
                'value': self.value}

    def calculate_contents_fingerprint(self):
        return calculate_contents_fingerprint(
            self.get_fingerprintable_contents())

    @classmethod
    def _prefetch_for_filter(cls, queryset=None):
        if queryset is None:
            queryset = cls.objects.all()
        return queryset.prefetch_related('tags').\
            select_related('file_resource')


class FileResource(BaseModel):

    NAME_FIELD = 'filename'
    HASH_FIELD = 'md5'
    ID_FIELD = 'data_object__uuid'
    TAG_FIELD = 'data_object__tags__tag'

    UPLOAD_STATUS_CHOICES = (('incomplete', 'Incomplete'),
                             ('complete', 'Complete'),
                             ('failed', 'Failed'),
                             ('deleting', 'Deleting'),
    )
    SOURCE_TYPE_CHOICES = (('imported', 'Imported'),
                           ('result', 'Result'),
                           ('log', 'Log'))

    data_object = models.OneToOneField(
        'DataObject',
        null=True,
        blank=True,
        related_name='file_resource',
        on_delete=models.SET_NULL)
    filename = models.CharField(
        max_length=255, validators=[validators.validate_filename])
    file_url = models.TextField(
        validators=[validators.validate_url])
    file_relative_path = models.TextField(
        validators=[validators.validate_relative_file_path], default='', blank=True)
    md5 = models.CharField(
        max_length=32, validators=[validators.validate_md5])
    import_comments = models.TextField(blank=True)
    imported_from_url = models.TextField(
        blank=True,
        validators=[validators.validate_url])
    upload_status = models.CharField(
        max_length=16,
        default='incomplete',
        choices=UPLOAD_STATUS_CHOICES)
    source_type = models.CharField(
        max_length=16,
        choices=SOURCE_TYPE_CHOICES)
    link = models.BooleanField(default=False)

    def get_fingerprintable_contents(self):
        return {'filename': self.filename,
                'md5': self.md5}

    @property
    def is_ready(self):
        return self.upload_status == 'complete'

    def get_uuid(self):
        if not self.data_object:
            return ''
        else:
            return self.data_object.uuid

    @classmethod
    def initialize(cls, **kwargs):
        if not kwargs.get('file_url'):
            file_root = cls.get_file_root()
            file_relative_path = kwargs.setdefault(
                'file_relative_path',
                cls._get_relative_path_for_import(
                    kwargs.get('filename'),
                    kwargs.get('source_type'),
                    kwargs.get('data_object'),
                    kwargs.pop('task_attempt', None)
                ))
            kwargs['file_url'] = os.path.join(file_root, file_relative_path)
            kwargs['file_relative_path'] = file_relative_path
        file_resource = cls(**kwargs)
        return file_resource

    @classmethod
    def _get_relative_path_for_import(
            cls, filename, source_type, data_object, task_attempt):
        parts = cls._get_run_breadcrumbs(source_type, data_object, task_attempt)
        parts.append(cls._get_subdir(source_type))
        parts.append(cls._get_expanded_filename(
            filename, data_object.uuid, source_type))
        return os.path.join(*parts)

    @classmethod
    def get_file_root(cls):
        file_root = get_setting('STORAGE_ROOT')
        assert file_root.startswith('/'), \
            'STORAGE_ROOT should be an absolute path, but it is "%s".' \
            % file_root
        return cls._add_url_prefix(file_root)

    @classmethod
    def _get_subdir(cls, source_type):
        if source_type == 'imported':
            return 'imported'
        if source_type == 'log':
            return 'logs'
        elif source_type == 'result':
            return 'work'
        else:
            assert False, 'Invalid source_type %s' % source_type

    @classmethod
    def _get_run_breadcrumbs(cls, source_type, data_object, task_attempt):
        """Create a path for a given file, in such a way
        that files end up being organized and browsable by run
        """
        # We cannot generate the path unless connect to a TaskAttempt
        # and a run
        if not task_attempt:
            return []
        # If multiple tasks exist, use the original.
        task = task_attempt.tasks.earliest('datetime_created')
        if task is None:
            return []
        run = task.run
        if run is None:
            return []

        breadcrumbs = [
            run.name,
            "task-%s" % str(task.uuid)[0:8],
            "attempt-%s" % str(task_attempt.uuid)[0:8],
        ]

        # Include any ancestors if run is nested
        while run.parent is not None:
            run = run.parent
            breadcrumbs = [run.name] + breadcrumbs

        # Prepend first breadcrumb with datetime and id
        breadcrumbs[0] = "%s-%s-%s" % (
            run.datetime_created.strftime('%Y-%m-%dT%H.%M.%SZ'),
            str(run.uuid)[0:8],
            breadcrumbs[0])

        breadcrumbs = ['runs'] + breadcrumbs
        return breadcrumbs

    @classmethod
    def _get_expanded_filename(cls, filename, data_object_uuid, source_type):
        if source_type == 'imported':
            return "%s_%s_%s" % (
                timezone.now().strftime('%Y-%m-%dT%H.%M.%SZ'),
                str(data_object_uuid)[0:8],
                filename)
        else:
            return filename

    @classmethod
    def _add_url_prefix(cls, path):
        if not path.startswith('/'):
            raise ValidationError(
                'Expected an absolute path but got path="%s"' % path)
        storage_type = get_setting('STORAGE_TYPE')
        if storage_type.lower() == 'local':
            return 'file://' + path
        elif storage_type.lower() == 'google_storage':
            return 'gs://' + get_setting('GOOGLE_STORAGE_BUCKET') + path
        else:
            raise ValidationError(
                'Couldn\'t recognize value for setting STORAGE_TYPE="%s"'\
                % storage_type)

    @classmethod
    def _prefetch_for_filter(cls, queryset=None):
        if queryset is None:
            queryset = cls.objects.all()
        return queryset.select_related('data_object').\
            prefetch_related('data_object__tags')
