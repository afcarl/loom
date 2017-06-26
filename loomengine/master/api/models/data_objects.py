from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
import jsonfield
import os

from .base import BaseModel
from api import get_setting
from api.models import uuidstr
from api.models import validators


class DataObject(BaseModel):

    NAME_FIELD = 'file_resource__filename'
    HASH_FIELD = 'file_resource__md5'
    ID_FIELD = 'uuid'

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
            return DataObject.objects.create(data={'value': value}, type=type)

    @classmethod
    def _get_file_by_value(cls, value):
        """Look up a file DataObject by name, uuid, and/or md5.
        """
        matches = FileResource.filter_by_name_or_id_or_hash(value)
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
        data_object = cls.objects.create(type='file')
        kwargs['data_object'] = data_object
        FileResource.initialize(**kwargs)
        return data_object


class FileResource(BaseModel):

    NAME_FIELD = 'filename'
    HASH_FIELD = 'md5'
    ID_FIELD = 'data_object__uuid'

    UPLOAD_STATUS_CHOICES = (('incomplete', 'Incomplete'),
                             ('complete', 'Complete'),
                             ('failed', 'Failed'))
    SOURCE_TYPE_CHOICES = (('imported', 'Imported'),
                           ('result', 'Result'),
                           ('log', 'Log'))

    data_object = models.OneToOneField(
        'DataObject',
        related_name='file_resource',
        on_delete=models.PROTECT)
    filename = models.CharField(
        max_length=255, validators=[validators.validate_filename])
    file_url = models.TextField(
        validators=[validators.validate_url])
    md5 = models.CharField(
        max_length=32, validators=[validators.validate_md5])
    import_comments = models.TextField(null=True, blank=True)
    imported_from_url = models.TextField(
        null=True, blank=True,
        validators=[validators.validate_url])
    upload_status = models.CharField(
        max_length=16,
        default='incomplete',
        choices=UPLOAD_STATUS_CHOICES)
    source_type = models.CharField(
        max_length=16,
        choices=SOURCE_TYPE_CHOICES)

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
            kwargs['file_url'] = cls._add_url_prefix(
                cls._get_path_for_import(
                    kwargs.get('filename'),
                    kwargs.get('source_type'),
                    kwargs.get('data_object')))
        return cls.objects.create(**kwargs)

    @classmethod
    def _get_path_for_import(cls, filename, source_type, data_object):
        parts = [cls._get_file_root()]
        parts.extend(cls._get_breadcrumbs(source_type, data_object))
        parts.append(cls._get_subdir(source_type))
        parts.append(cls._get_expanded_filename(filename, data_object.uuid))
        return os.path.join(*parts)

    @classmethod
    def _get_file_root(cls):
        file_root = get_setting('LOOM_STORAGE_ROOT')
        # Allow '~/path' home dir notation on local file server
        if get_setting('LOOM_STORAGE_TYPE') == 'LOCAL':
            file_root = os.path.expanduser(file_root)
        assert file_root.startswith('/'), \
            'LOOM_STORAGE_ROOT should be an absolute path, but it is "%s".' \
            % file_root
        return file_root

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
    def _get_breadcrumbs(cls, source_type, data_object):
        """Create a path for a given file, in such a way
        that files end up being organized and browsable by run
        """

        # We should only be here if the file is connected to a TaskAttempt
        if not source_type in ['log', 'work']:
            return []

        if source_type == 'log':
            task_attempt \
                = data_object.task_attempt_log_file.task_attempt
        elif source_type == 'result':
            task_attempt \
                = data_object.task_attempt_output.task_attempt

        task = task_attempt.task
        run = task.run
        breadcrumbs = ["%s-%s" % (str(run.uuid)[0:8], run.name),
                       "task-%s" % str(task.uuid)[0:8],
                       "attempt-%s" % str(task_attempt.uuid)[0:8]]
        while run.parent is not None:
            run = run.parent
            breadcrumbs = [
                "%s-%s" % (str(run.uuid)[0:8], run.name)] \
                + breadcrumbs
        # Prepend first run with datetime
        breadcrumbs[0] = "%s-%s" % (
            run.datetime_created.strftime('%Y-%m-%dT%H.%M.%SZ'),
            breadcrumbs[0])
        return breadcrumbs

    @classmethod
    def _get_expanded_filename(cls, filename, data_object_uuid):
        return "%s_%s_%s" % (
            timezone.now().strftime('%Y-%m-%dT%H.%M.%SZ'),
            str(data_object_uuid)[0:8],
            filename)

    @classmethod
    def _add_url_prefix(cls, path):
        if not path.startswith('/'):
            raise ValidationError(
                'Expected an absolute path but got path="%s"' % path)
        LOOM_STORAGE_TYPE = get_setting('LOOM_STORAGE_TYPE')
        if LOOM_STORAGE_TYPE == 'LOCAL':
            return 'file://' + path
        elif LOOM_STORAGE_TYPE == 'GOOGLE_STORAGE':
            return 'gs://' + get_setting('GOOGLE_STORAGE_BUCKET') + path
        else:
            raise ValidationError(
                'Couldn\'t recognize value for setting LOOM_STORAGE_TYPE="%s"'\
                % LOOM_STORAGE_TYPE)
