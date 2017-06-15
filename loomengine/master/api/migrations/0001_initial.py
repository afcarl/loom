# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-06-14 21:49
from __future__ import unicode_literals

import api.models
import api.models.base
import api.models.data_tree_nodes
import api.models.templates
import api.models.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import jsonfield.fields
import mptt.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ArrayMembership',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('order', models.IntegerField()),
            ],
            options={
                'ordering': ['order'],
            },
            bases=(models.Model, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='DataObject',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('uuid', models.CharField(default=api.models.uuidstr, max_length=255, unique=True)),
                ('type', models.CharField(choices=[(b'boolean', b'Boolean'), (b'file', b'File'), (b'float', b'Float'), (b'integer', b'Integer'), (b'string', b'String')], max_length=255)),
                ('is_array', models.BooleanField(default=False)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='DataTreeNode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('uuid', models.CharField(default=api.models.uuidstr, max_length=255, unique=True)),
                ('index', models.IntegerField(blank=True, null=True)),
                ('degree', models.IntegerField(blank=True, null=True, validators=[api.models.data_tree_nodes.degree_validator])),
                ('type', models.CharField(choices=[(b'boolean', b'Boolean'), (b'file', b'File'), (b'float', b'Float'), (b'integer', b'Integer'), (b'string', b'String')], max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='FileResource',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('uuid', models.CharField(default=api.models.uuidstr, max_length=255, unique=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('file_url', models.CharField(max_length=1000)),
                ('md5', models.CharField(blank=True, max_length=255, null=True)),
                ('upload_status', models.CharField(choices=[(b'incomplete', b'Incomplete'), (b'complete', b'Complete'), (b'failed', b'Failed')], default=b'incomplete', max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='FixedInput',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('channel', models.CharField(max_length=255)),
                ('type', models.CharField(choices=[(b'boolean', b'Boolean'), (b'file', b'File'), (b'float', b'Float'), (b'integer', b'Integer'), (b'string', b'String')], max_length=255)),
                ('mode', models.CharField(max_length=255)),
                ('group', models.IntegerField()),
                ('data_root', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.DataTreeNode')),
            ],
            bases=(models.Model, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='Run',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('uuid', models.CharField(default=api.models.uuidstr, editable=False, max_length=255, unique=True)),
                ('name', models.CharField(max_length=255)),
                ('is_leaf', models.BooleanField()),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('datetime_finished', models.DateTimeField(blank=True, null=True)),
                ('postprocessing_status', models.CharField(choices=[(b'not_started', b'Not Started'), (b'in_progress', b'In Progress'), (b'complete', b'Complete'), (b'failed', b'Failed')], default=b'not_started', max_length=255)),
                ('status_is_finished', models.BooleanField(default=False)),
                ('status_is_failed', models.BooleanField(default=False)),
                ('status_is_killed', models.BooleanField(default=False)),
                ('status_is_running', models.BooleanField(default=False)),
                ('status_is_waiting', models.BooleanField(default=True)),
                ('command', models.TextField(blank=True, null=True)),
                ('interpreter', models.CharField(blank=True, max_length=1024, null=True)),
                ('lft', models.PositiveIntegerField(db_index=True, editable=False)),
                ('rght', models.PositiveIntegerField(db_index=True, editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(db_index=True, editable=False)),
                ('parent', mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='steps', to='api.Run')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='RunConnectorNode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('channel', models.CharField(max_length=255)),
                ('type', models.CharField(choices=[(b'boolean', b'Boolean'), (b'file', b'File'), (b'float', b'Float'), (b'integer', b'Integer'), (b'string', b'String')], max_length=255)),
                ('data_root', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.DataTreeNode')),
                ('run', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='connectors', to='api.Run')),
            ],
            bases=(models.Model, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='RunInput',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('channel', models.CharField(max_length=255)),
                ('type', models.CharField(choices=[(b'boolean', b'Boolean'), (b'file', b'File'), (b'float', b'Float'), (b'integer', b'Integer'), (b'string', b'String')], max_length=255)),
                ('mode', models.CharField(blank=True, max_length=255, null=True)),
                ('group', models.IntegerField(blank=True, null=True)),
                ('data_root', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.DataTreeNode')),
                ('run', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='inputs', to='api.Run')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='RunOutput',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('channel', models.CharField(max_length=255)),
                ('type', models.CharField(choices=[(b'boolean', b'Boolean'), (b'file', b'File'), (b'float', b'Float'), (b'integer', b'Integer'), (b'string', b'String')], max_length=255)),
                ('mode', models.CharField(blank=True, max_length=255, null=True)),
                ('source', jsonfield.fields.JSONField(blank=True, null=True)),
                ('parser', jsonfield.fields.JSONField(blank=True, null=True, validators=[api.models.validators.task_output_parser_validator])),
                ('data_root', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.DataTreeNode')),
                ('run', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='outputs', to='api.Run')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='RunRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('run', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='run_request', to='api.Run')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='RunRequestInput',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('channel', models.CharField(max_length=255)),
                ('type', models.CharField(choices=[(b'boolean', b'Boolean'), (b'file', b'File'), (b'float', b'Float'), (b'integer', b'Integer'), (b'string', b'String')], max_length=255)),
                ('data_root', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.DataTreeNode')),
                ('run_request', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inputs', to='api.RunRequest')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='RunTimepoint',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('message', models.CharField(max_length=255)),
                ('detail', models.TextField(blank=True, null=True)),
                ('is_error', models.BooleanField(default=False)),
                ('run', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='timepoints', to='api.Run')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('uuid', models.CharField(default=api.models.uuidstr, editable=False, max_length=255, unique=True)),
                ('interpreter', models.CharField(max_length=1024)),
                ('command', models.TextField()),
                ('rendered_command', models.TextField(blank=True, null=True)),
                ('environment', jsonfield.fields.JSONField()),
                ('resources', jsonfield.fields.JSONField()),
                ('data_path', jsonfield.fields.JSONField(blank=True, null=True, validators=[api.models.validators.task_data_path_validator])),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('datetime_finished', models.DateTimeField(blank=True, null=True)),
                ('status_is_finished', models.BooleanField(default=False)),
                ('status_is_failed', models.BooleanField(default=False)),
                ('status_is_killed', models.BooleanField(default=False)),
                ('status_is_running', models.BooleanField(default=False)),
                ('status_is_waiting', models.BooleanField(default=True)),
                ('run', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='api.Run')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='TaskAttempt',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('uuid', models.CharField(default=api.models.uuidstr, editable=False, max_length=255, unique=True)),
                ('interpreter', models.CharField(max_length=1024)),
                ('rendered_command', models.TextField()),
                ('environment', jsonfield.fields.JSONField()),
                ('resources', jsonfield.fields.JSONField()),
                ('parser', jsonfield.fields.JSONField(blank=True, null=True, validators=[api.models.validators.task_output_parser_validator])),
                ('last_heartbeat', models.DateTimeField(auto_now=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('datetime_finished', models.DateTimeField(blank=True, null=True)),
                ('status_is_finished', models.BooleanField(default=False)),
                ('status_is_failed', models.BooleanField(default=False)),
                ('status_is_killed', models.BooleanField(default=False)),
                ('status_is_running', models.BooleanField(default=True)),
                ('status_is_cleaned_up', models.BooleanField(default=False)),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='task_attempts', to='api.Task')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='TaskAttemptInput',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('channel', models.CharField(max_length=255)),
                ('type', models.CharField(choices=[(b'boolean', b'Boolean'), (b'file', b'File'), (b'float', b'Float'), (b'integer', b'Integer'), (b'string', b'String')], max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='TaskAttemptLogFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('uuid', models.CharField(default=api.models.uuidstr, editable=False, max_length=255, unique=True)),
                ('log_name', models.CharField(max_length=255)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='TaskAttemptOutput',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('channel', models.CharField(max_length=255)),
                ('type', models.CharField(choices=[(b'boolean', b'Boolean'), (b'file', b'File'), (b'float', b'Float'), (b'integer', b'Integer'), (b'string', b'String')], max_length=255)),
                ('mode', models.CharField(blank=True, max_length=255, null=True)),
                ('source', jsonfield.fields.JSONField(blank=True, null=True)),
                ('parser', jsonfield.fields.JSONField(blank=True, null=True, validators=[api.models.validators.task_output_parser_validator])),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='TaskAttemptTimepoint',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('message', models.CharField(max_length=255)),
                ('detail', models.TextField(blank=True, null=True)),
                ('is_error', models.BooleanField(default=False)),
                ('task_attempt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='timepoints', to='api.TaskAttempt')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='TaskInput',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('channel', models.CharField(max_length=255)),
                ('type', models.CharField(choices=[(b'boolean', b'Boolean'), (b'file', b'File'), (b'float', b'Float'), (b'integer', b'Integer'), (b'string', b'String')], max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='TaskOutput',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('channel', models.CharField(max_length=255)),
                ('type', models.CharField(choices=[(b'boolean', b'Boolean'), (b'file', b'File'), (b'float', b'Float'), (b'integer', b'Integer'), (b'string', b'String')], max_length=255)),
                ('mode', models.CharField(blank=True, max_length=255, null=True)),
                ('source', jsonfield.fields.JSONField(blank=True, null=True)),
                ('parser', jsonfield.fields.JSONField(blank=True, null=True, validators=[api.models.validators.task_output_parser_validator])),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='TaskTimepoint',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('message', models.CharField(max_length=255)),
                ('detail', models.TextField(blank=True, null=True)),
                ('is_error', models.BooleanField(default=False)),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='timepoints', to='api.Task')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='Template',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('uuid', models.CharField(default=api.models.uuidstr, editable=False, max_length=255, unique=True)),
                ('name', models.CharField(max_length=255)),
                ('is_leaf', models.BooleanField()),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('postprocessing_status', models.CharField(choices=[(b'incomplete', b'Incomplete'), (b'complete', b'Complete'), (b'failed', b'Failed')], default=b'incomplete', max_length=255)),
                ('command', models.TextField(blank=True)),
                ('interpreter', models.CharField(blank=True, max_length=1024)),
                ('environment', jsonfield.fields.JSONField(blank=True, null=True, validators=[api.models.templates.environment_validator])),
                ('resources', jsonfield.fields.JSONField(blank=True, null=True, validators=[api.models.templates.resources_validator])),
                ('template_import', jsonfield.fields.JSONField(blank=True, null=True, validators=[api.models.templates.template_import_validator])),
                ('outputs', jsonfield.fields.JSONField(blank=True, null=True, validators=[api.models.templates.outputs_validator])),
                ('inputs', jsonfield.fields.JSONField(blank=True, null=True, validators=[api.models.templates.inputs_validator])),
                ('raw_data', jsonfield.fields.JSONField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='TemplateMembership',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('child_template', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='parents', to='api.Template')),
                ('parent_template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='children', to='api.Template')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='ArrayDataObject',
            fields=[
                ('dataobject_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='api.DataObject')),
            ],
            options={
                'abstract': False,
            },
            bases=('api.dataobject',),
        ),
        migrations.CreateModel(
            name='BooleanDataObject',
            fields=[
                ('dataobject_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='api.DataObject')),
                ('value', models.BooleanField()),
            ],
            options={
                'abstract': False,
            },
            bases=('api.dataobject',),
        ),
        migrations.CreateModel(
            name='FileDataObject',
            fields=[
                ('dataobject_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='api.DataObject')),
                ('filename', models.CharField(max_length=1024)),
                ('md5', models.CharField(blank=True, max_length=255, null=True)),
                ('source_type', models.CharField(choices=[(b'imported', b'Imported'), (b'result', b'Result'), (b'log', b'Log')], max_length=255)),
                ('file_import', jsonfield.fields.JSONField(blank=True, null=True)),
                ('file_resource', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='file_data_objects', to='api.FileResource')),
            ],
            options={
                'abstract': False,
            },
            bases=('api.dataobject',),
        ),
        migrations.CreateModel(
            name='FloatDataObject',
            fields=[
                ('dataobject_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='api.DataObject')),
                ('value', models.FloatField()),
            ],
            options={
                'abstract': False,
            },
            bases=('api.dataobject',),
        ),
        migrations.CreateModel(
            name='IntegerDataObject',
            fields=[
                ('dataobject_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='api.DataObject')),
                ('value', models.IntegerField()),
            ],
            options={
                'abstract': False,
            },
            bases=('api.dataobject',),
        ),
        migrations.CreateModel(
            name='StringDataObject',
            fields=[
                ('dataobject_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='api.DataObject')),
                ('value', models.TextField(max_length=10000)),
            ],
            options={
                'abstract': False,
            },
            bases=('api.dataobject',),
        ),
        migrations.AddField(
            model_name='template',
            name='steps',
            field=models.ManyToManyField(related_name='templates', through='api.TemplateMembership', to='api.Template'),
        ),
        migrations.AddField(
            model_name='taskoutput',
            name='data_object',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='api.DataObject'),
        ),
        migrations.AddField(
            model_name='taskoutput',
            name='task',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='outputs', to='api.Task'),
        ),
        migrations.AddField(
            model_name='taskinput',
            name='data_object',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='api.DataObject'),
        ),
        migrations.AddField(
            model_name='taskinput',
            name='task',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inputs', to='api.Task'),
        ),
        migrations.AddField(
            model_name='taskattemptoutput',
            name='data_object',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='task_attempt_output', to='api.DataObject'),
        ),
        migrations.AddField(
            model_name='taskattemptoutput',
            name='task_attempt',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='outputs', to='api.TaskAttempt'),
        ),
        migrations.AddField(
            model_name='taskattemptlogfile',
            name='file',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='task_attempt_log_file', to='api.DataObject'),
        ),
        migrations.AddField(
            model_name='taskattemptlogfile',
            name='task_attempt',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='log_files', to='api.TaskAttempt'),
        ),
        migrations.AddField(
            model_name='taskattemptinput',
            name='data_object',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='api.DataObject'),
        ),
        migrations.AddField(
            model_name='taskattemptinput',
            name='task_attempt',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inputs', to='api.TaskAttempt'),
        ),
        migrations.AddField(
            model_name='task',
            name='selected_task_attempt',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='task_as_selected', to='api.TaskAttempt'),
        ),
        migrations.AddField(
            model_name='runrequest',
            name='template',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='api.Template'),
        ),
        migrations.AddField(
            model_name='run',
            name='template',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='runs', to='api.Template'),
        ),
        migrations.AddField(
            model_name='fixedinput',
            name='template',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fixed_inputs', to='api.Template'),
        ),
        migrations.AddField(
            model_name='datatreenode',
            name='data_object',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='data_tree_nodes', to='api.DataObject'),
        ),
        migrations.AddField(
            model_name='datatreenode',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='children', to='api.DataTreeNode'),
        ),
        migrations.AddField(
            model_name='datatreenode',
            name='root_node',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='descendants', to='api.DataTreeNode'),
        ),
        migrations.AddField(
            model_name='arraymembership',
            name='member',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='in_array_membership', to='api.DataObject'),
        ),
        migrations.AlterUniqueTogether(
            name='runconnectornode',
            unique_together=set([('run', 'channel')]),
        ),
        migrations.AddField(
            model_name='arraymembership',
            name='array',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='has_array_members_membership', to='api.ArrayDataObject'),
        ),
        migrations.AddField(
            model_name='arraydataobject',
            name='prefetch_members',
            field=models.ManyToManyField(related_name='arrays', through='api.ArrayMembership', to='api.DataObject'),
        ),
    ]
