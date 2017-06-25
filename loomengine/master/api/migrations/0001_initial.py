# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-06-25 06:19
from __future__ import unicode_literals

import api.models
import api.models.base
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
            name='DataNode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('uuid', models.CharField(default=api.models.uuidstr, max_length=255, unique=True)),
                ('index', models.IntegerField(blank=True, null=True)),
                ('degree', models.IntegerField(blank=True, null=True, validators=[api.models.validators.validate_ge0])),
                ('type', models.CharField(choices=[(b'boolean', b'Boolean'), (b'file', b'File'), (b'float', b'Float'), (b'integer', b'Integer'), (b'string', b'String')], max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='DataObject',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('uuid', models.CharField(default=api.models.uuidstr, max_length=255, unique=True)),
                ('type', models.CharField(choices=[(b'boolean', b'Boolean'), (b'file', b'File'), (b'float', b'Float'), (b'integer', b'Integer'), (b'string', b'String')], max_length=16)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('data', jsonfield.fields.JSONField(blank=True)),
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
                ('filename', models.CharField(max_length=255, validators=[api.models.validators.validate_filename])),
                ('file_url', models.TextField(validators=[api.models.validators.validate_url])),
                ('md5', models.CharField(max_length=32, validators=[api.models.validators.validate_md5])),
                ('import_comments', models.TextField(blank=True, null=True)),
                ('imported_from_url', models.TextField(blank=True, null=True, validators=[api.models.validators.validate_url])),
                ('upload_status', models.CharField(choices=[(b'incomplete', b'Incomplete'), (b'complete', b'Complete'), (b'failed', b'Failed')], default=b'incomplete', max_length=16)),
                ('source_type', models.CharField(choices=[(b'imported', b'Imported'), (b'result', b'Result'), (b'log', b'Log')], max_length=16)),
                ('data_object', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='file_resource', to='api.DataObject')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='RequestedInput',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('channel', models.CharField(max_length=255)),
                ('type', models.CharField(choices=[(b'boolean', b'Boolean'), (b'file', b'File'), (b'float', b'Float'), (b'integer', b'Integer'), (b'string', b'String')], max_length=255)),
                ('data_tree', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.DataNode')),
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
                ('data_tree', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.DataNode')),
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
                ('data_tree', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.DataNode')),
                ('run', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='inputs', to='api.Run')),
            ],
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
                ('parser', jsonfield.fields.JSONField(blank=True, null=True, validators=[api.models.validators.OutputParserValidator.validate_output_parser])),
                ('data_tree', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.DataNode')),
                ('run', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='outputs', to='api.Run')),
            ],
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
                ('data_path', jsonfield.fields.JSONField(blank=True, null=True, validators=[api.models.validators.validate_data_path])),
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
                ('last_heartbeat', models.DateTimeField(auto_now=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('datetime_finished', models.DateTimeField(blank=True, null=True)),
                ('status_is_finished', models.BooleanField(default=False)),
                ('status_is_failed', models.BooleanField(default=False)),
                ('status_is_killed', models.BooleanField(default=False)),
                ('status_is_running', models.BooleanField(default=True)),
                ('status_is_cleaned_up', models.BooleanField(default=False)),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='task_attempt_set', to='api.Task')),
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
                ('data_tree', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.DataNode')),
                ('task_attempt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inputs', to='api.TaskAttempt')),
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
                ('file', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='task_attempt_log_file', to='api.DataObject')),
                ('task_attempt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='log_files', to='api.TaskAttempt')),
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
                ('parser', jsonfield.fields.JSONField(blank=True, null=True, validators=[api.models.validators.OutputParserValidator.validate_output_parser])),
                ('data_tree', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.DataNode')),
                ('task_attempt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='outputs', to='api.TaskAttempt')),
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
                ('data_tree', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.DataNode')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inputs', to='api.Task')),
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
                ('parser', jsonfield.fields.JSONField(blank=True, null=True, validators=[api.models.validators.OutputParserValidator.validate_output_parser])),
                ('data_tree', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.DataNode')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='outputs', to='api.Task')),
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
                ('name', models.CharField(max_length=255, validators=[api.models.validators.TemplateValidator.validate_name])),
                ('is_leaf', models.BooleanField()),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('postprocessing_status', models.CharField(choices=[(b'incomplete', b'Incomplete'), (b'complete', b'Complete'), (b'failed', b'Failed')], default=b'incomplete', max_length=255)),
                ('command', models.TextField(blank=True)),
                ('interpreter', models.CharField(blank=True, max_length=1024)),
                ('environment', jsonfield.fields.JSONField(blank=True, null=True, validators=[api.models.validators.validate_environment])),
                ('resources', jsonfield.fields.JSONField(blank=True, null=True, validators=[api.models.validators.validate_resources])),
                ('comments', models.TextField(blank=True, null=True)),
                ('import_comments', models.TextField(blank=True, null=True)),
                ('imported_from_url', models.TextField(blank=True, null=True, validators=[api.models.validators.validate_url])),
                ('imported', models.BooleanField(default=False)),
                ('outputs', jsonfield.fields.JSONField(blank=True, null=True, validators=[api.models.validators.TemplateValidator.validate_outputs])),
                ('raw_data', jsonfield.fields.JSONField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='TemplateInput',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('channel', models.CharField(max_length=255)),
                ('type', models.CharField(choices=[(b'boolean', b'Boolean'), (b'file', b'File'), (b'float', b'Float'), (b'integer', b'Integer'), (b'string', b'String')], max_length=255)),
                ('hint', models.CharField(blank=True, max_length=1000)),
                ('mode', models.CharField(max_length=255)),
                ('group', models.IntegerField(blank=True, null=True)),
                ('data_tree', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.DataNode')),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inputs', to='api.Template')),
            ],
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
            name='TemplateNode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('lft', models.PositiveIntegerField(db_index=True, editable=False)),
                ('rght', models.PositiveIntegerField(db_index=True, editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(db_index=True, editable=False)),
                ('parent', mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='children', to='api.TemplateNode')),
                ('template', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='template_nodes', to='api.Template')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._FilterMixin),
        ),
        migrations.AddField(
            model_name='template',
            name='steps',
            field=models.ManyToManyField(related_name='templates', through='api.TemplateMembership', to='api.Template'),
        ),
        migrations.AddField(
            model_name='task',
            name='task_attempt',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='acitve_task', to='api.TaskAttempt'),
        ),
        migrations.AddField(
            model_name='run',
            name='template',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='runs', to='api.Template'),
        ),
        migrations.AddField(
            model_name='requestedinput',
            name='run',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='requested_inputs', to='api.Run'),
        ),
        migrations.AddField(
            model_name='datanode',
            name='data_object',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='data_nodes', to='api.DataObject'),
        ),
        migrations.AddField(
            model_name='datanode',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='api.DataNode'),
        ),
        migrations.AlterUniqueTogether(
            name='runoutput',
            unique_together=set([('run', 'channel')]),
        ),
        migrations.AlterUniqueTogether(
            name='runinput',
            unique_together=set([('run', 'channel')]),
        ),
        migrations.AlterUniqueTogether(
            name='runconnectornode',
            unique_together=set([('run', 'channel')]),
        ),
        migrations.AlterUniqueTogether(
            name='requestedinput',
            unique_together=set([('run', 'channel')]),
        ),
    ]
