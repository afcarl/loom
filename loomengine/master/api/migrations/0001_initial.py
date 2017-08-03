# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-08-01 21:15
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
            name='DataLabel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('label', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='DataNode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('uuid', models.CharField(default=api.models.uuidstr, max_length=255, unique=True)),
                ('index', models.IntegerField(blank=True, null=True)),
                ('degree', models.IntegerField(blank=True, null=True, validators=[api.models.validators.validate_ge0])),
                ('type', models.CharField(choices=[(b'boolean', b'Boolean'), (b'file', b'File'), (b'float', b'Float'), (b'integer', b'Integer'), (b'string', b'String')], max_length=255)),
                ('lft', models.PositiveIntegerField(db_index=True, editable=False)),
                ('rght', models.PositiveIntegerField(db_index=True, editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(db_index=True, editable=False)),
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
            name='DataTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('tag', models.CharField(max_length=255, unique=True)),
                ('data_object', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tags', to='api.DataObject')),
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
                ('import_comments', models.TextField(blank=True)),
                ('imported_from_url', models.TextField(blank=True, validators=[api.models.validators.validate_url])),
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
            name='Run',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('uuid', models.CharField(default=api.models.uuidstr, editable=False, max_length=255, unique=True)),
                ('name', models.CharField(max_length=255)),
                ('is_leaf', models.BooleanField()),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('datetime_finished', models.DateTimeField(blank=True, null=True)),
                ('environment', jsonfield.fields.JSONField(blank=True, validators=[api.models.validators.validate_environment])),
                ('resources', jsonfield.fields.JSONField(blank=True, validators=[api.models.validators.validate_resources])),
                ('notification_addresses', jsonfield.fields.JSONField(blank=True, validators=[api.models.validators.validate_notification_addresses])),
                ('postprocessing_status', models.CharField(choices=[(b'not_started', b'Not Started'), (b'in_progress', b'In Progress'), (b'complete', b'Complete'), (b'failed', b'Failed')], default=b'not_started', max_length=255)),
                ('status_is_finished', models.BooleanField(default=False)),
                ('status_is_failed', models.BooleanField(default=False)),
                ('status_is_killed', models.BooleanField(default=False)),
                ('status_is_running', models.BooleanField(default=False)),
                ('status_is_waiting', models.BooleanField(default=True)),
                ('command', models.TextField(blank=True)),
                ('interpreter', models.CharField(blank=True, max_length=1024)),
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
                ('has_source', models.BooleanField(default=False)),
                ('data_node', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.DataNode')),
                ('run', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='connectors', to='api.Run')),
            ],
            bases=(models.Model, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='RunEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('event', models.CharField(max_length=255)),
                ('detail', models.TextField(blank=True)),
                ('is_error', models.BooleanField(default=False)),
                ('run', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='api.Run')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='RunInput',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('channel', models.CharField(max_length=255)),
                ('type', models.CharField(choices=[(b'boolean', b'Boolean'), (b'file', b'File'), (b'float', b'Float'), (b'integer', b'Integer'), (b'string', b'String')], max_length=255)),
                ('mode', models.CharField(blank=True, max_length=255)),
                ('group', models.IntegerField(blank=True, null=True)),
                ('as_channel', models.CharField(blank=True, max_length=255, null=True)),
                ('data_node', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.DataNode')),
                ('run', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='inputs', to='api.Run')),
            ],
            bases=(models.Model, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='RunLabel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('label', models.CharField(max_length=255)),
                ('run', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='labels', to='api.Run')),
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
                ('mode', models.CharField(blank=True, max_length=255)),
                ('source', jsonfield.fields.JSONField(blank=True)),
                ('parser', jsonfield.fields.JSONField(blank=True, validators=[api.models.validators.OutputParserValidator.validate_output_parser])),
                ('as_channel', models.CharField(blank=True, max_length=255, null=True)),
                ('data_node', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.DataNode')),
                ('run', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='outputs', to='api.Run')),
            ],
            bases=(models.Model, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='RunTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('tag', models.CharField(max_length=255, unique=True)),
                ('run', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tags', to='api.Run')),
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
                ('raw_command', models.TextField()),
                ('command', models.TextField(blank=True)),
                ('environment', jsonfield.fields.JSONField()),
                ('resources', jsonfield.fields.JSONField(blank=True)),
                ('data_path', jsonfield.fields.JSONField(blank=True, validators=[api.models.validators.validate_data_path])),
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
                ('command', models.TextField()),
                ('environment', jsonfield.fields.JSONField()),
                ('environment_info', jsonfield.fields.JSONField(blank=True)),
                ('resources', jsonfield.fields.JSONField(blank=True)),
                ('resources_info', jsonfield.fields.JSONField(blank=True)),
                ('last_heartbeat', models.DateTimeField(auto_now=True)),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('datetime_finished', models.DateTimeField(blank=True, null=True)),
                ('status_is_finished', models.BooleanField(default=False)),
                ('status_is_failed', models.BooleanField(default=False)),
                ('status_is_killed', models.BooleanField(default=False)),
                ('status_is_running', models.BooleanField(default=True)),
                ('status_is_cleaned_up', models.BooleanField(default=False)),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='all_task_attempts', to='api.Task')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='TaskAttemptEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('event', models.CharField(max_length=255)),
                ('detail', models.TextField(blank=True)),
                ('is_error', models.BooleanField(default=False)),
                ('task_attempt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='api.TaskAttempt')),
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
                ('mode', models.CharField(max_length=255)),
                ('data_node', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.DataNode')),
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
                ('data_object', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='task_attempt_log_file', to='api.DataObject')),
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
                ('uuid', models.CharField(default=api.models.uuidstr, editable=False, max_length=255, unique=True)),
                ('mode', models.CharField(max_length=255)),
                ('source', jsonfield.fields.JSONField(blank=True)),
                ('parser', jsonfield.fields.JSONField(blank=True, validators=[api.models.validators.OutputParserValidator.validate_output_parser])),
                ('data_node', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.DataNode')),
                ('task_attempt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='outputs', to='api.TaskAttempt')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='TaskEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('event', models.CharField(max_length=255)),
                ('detail', models.TextField(blank=True)),
                ('is_error', models.BooleanField(default=False)),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='api.Task')),
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
                ('mode', models.CharField(max_length=255)),
                ('as_channel', models.CharField(blank=True, max_length=255, null=True)),
                ('data_node', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.DataNode')),
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
                ('mode', models.CharField(max_length=255)),
                ('source', jsonfield.fields.JSONField(blank=True)),
                ('parser', jsonfield.fields.JSONField(blank=True, validators=[api.models.validators.OutputParserValidator.validate_output_parser])),
                ('as_channel', models.CharField(blank=True, max_length=255, null=True)),
                ('data_node', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.DataNode')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='outputs', to='api.Task')),
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
                ('md5', models.CharField(blank=True, max_length=32, null=True, validators=[api.models.validators.validate_md5])),
                ('is_leaf', models.BooleanField()),
                ('datetime_created', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('command', models.TextField(blank=True)),
                ('interpreter', models.CharField(blank=True, max_length=1024)),
                ('environment', jsonfield.fields.JSONField(blank=True, validators=[api.models.validators.validate_environment])),
                ('resources', jsonfield.fields.JSONField(blank=True, validators=[api.models.validators.validate_resources])),
                ('comments', models.TextField(blank=True)),
                ('import_comments', models.TextField(blank=True)),
                ('imported_from_url', models.TextField(blank=True, validators=[api.models.validators.validate_url])),
                ('imported', models.BooleanField(default=False)),
                ('outputs', jsonfield.fields.JSONField(blank=True, validators=[api.models.validators.TemplateValidator.validate_outputs])),
                ('raw_data', jsonfield.fields.JSONField(blank=True)),
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
                ('mode', models.CharField(blank=True, max_length=255)),
                ('group', models.IntegerField(blank=True, null=True)),
                ('as_channel', models.CharField(blank=True, max_length=255, null=True)),
                ('data_node', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.DataNode')),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inputs', to='api.Template')),
            ],
            bases=(models.Model, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='TemplateLabel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('label', models.CharField(max_length=255)),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='labels', to='api.Template')),
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
            name='TemplateTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('tag', models.CharField(max_length=255, unique=True)),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tags', to='api.Template')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, api.models.base._FilterMixin),
        ),
        migrations.CreateModel(
            name='UserInput',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_change', models.IntegerField(default=0)),
                ('channel', models.CharField(max_length=255)),
                ('type', models.CharField(choices=[(b'boolean', b'Boolean'), (b'file', b'File'), (b'float', b'Float'), (b'integer', b'Integer'), (b'string', b'String')], max_length=255)),
                ('data_node', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.DataNode')),
                ('run', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_inputs', to='api.Run')),
            ],
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
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='active_task', to='api.TaskAttempt'),
        ),
        migrations.AddField(
            model_name='run',
            name='template',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='runs', to='api.Template'),
        ),
        migrations.AddField(
            model_name='datanode',
            name='data_object',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='data_nodes', to='api.DataObject'),
        ),
        migrations.AddField(
            model_name='datanode',
            name='parent',
            field=mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='api.DataNode'),
        ),
        migrations.AddField(
            model_name='datalabel',
            name='data_object',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='labels', to='api.DataObject'),
        ),
        migrations.AlterUniqueTogether(
            name='userinput',
            unique_together=set([('run', 'channel')]),
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
    ]
