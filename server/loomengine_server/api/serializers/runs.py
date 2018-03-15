import copy
from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import prefetch_related_objects
import django.db
from . import CreateWithParentModelSerializer, RecursiveField, \
    strip_empty_values, match_and_update_by_uuid, \
    reload_models, flatten_nodes, replace_nodes
from api.models.runs import Run, UserInput, RunInput, RunOutput, RunEvent
from api.models.tasks import Task, TaskInput, TaskOutput, TaskEvent
from api.models.task_attempts import TaskAttempt, TaskAttemptInput, TaskAttemptOutput, TaskAttemptEvent, TaskAttemptLogFile, TaskMembership
from api.serializers.data_objects import DataObjectSerializer
from api.serializers.templates import TemplateSerializer, URLTemplateSerializer
from api.serializers.tasks import TaskSerializer, URLTaskSerializer, \
    ExpandedTaskSerializer
from api.serializers.data_channels import DataChannelSerializer, \
    ExpandedDataChannelSerializer
from api.serializers.data_nodes import DataNodeSerializer, ExpandedDataNodeSerializer
from api import async


class UserInputSerializer(DataChannelSerializer):

    # type not required because it is inferred from template
    type = serializers.CharField(required=False)

    class Meta:
        model = UserInput
        fields = ('type', 'channel', 'data')


class ExpandedUserInputSerializer(ExpandedDataChannelSerializer):

    # type not required because it is inferred from template
    type = serializers.CharField(required=False)

    class Meta:
        model = UserInput
        fields = ('type', 'channel', 'data')

        
class RunInputSerializer(DataChannelSerializer):

    class Meta:
        model = RunInput
        fields = ('type', 'channel', 'as_channel', 'data', 'mode', 'group')

    mode = serializers.CharField(required=False)
    group = serializers.IntegerField(required=False)
    as_channel = serializers.CharField(required=False)

    def to_representation(self, instance):
        return strip_empty_values(
            super(RunInputSerializer, self).to_representation(instance))


class ExpandedRunInputSerializer(ExpandedDataChannelSerializer):

    class Meta:
        model = RunInput
        fields = ('type', 'channel', 'as_channel', 'data', 'mode', 'group')

    mode = serializers.CharField(required=False)
    group = serializers.IntegerField(required=False)
    as_channel = serializers.CharField(required=False)

    def to_representation(self, instance):
        return strip_empty_values(
            super(ExpandedRunInputSerializer, self).to_representation(instance))


class RunOutputSerializer(DataChannelSerializer):

    class Meta:
        model = RunOutput
        fields = ('type', 'channel', 'as_channel', 'data', 'mode', 'source', 'parser')

    mode = serializers.CharField(required=False)
    source = serializers.JSONField(required=False)
    parser = serializers.JSONField(required=False)
    as_channel = serializers.CharField(required=False)

    def to_representation(self, instance):
        return strip_empty_values(
            super(RunOutputSerializer, self).to_representation(instance))


class ExpandedRunOutputSerializer(ExpandedDataChannelSerializer):

    class Meta:
        model = RunOutput
        fields = ('type', 'channel', 'as_channel', 'data', 'mode', 'source', 'parser')

    mode = serializers.CharField(required=False)
    source = serializers.JSONField(required=False)
    parser = serializers.JSONField(required=False)
    as_channel = serializers.CharField(required=False)

    def to_representation(self, instance):
        return strip_empty_values(
            super(ExpandedRunOutputSerializer, self).to_representation(instance))


class RunEventSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = RunEvent
        fields = ('event', 'detail', 'timestamp', 'is_error')


class _AbstractWritableRunSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Run
	fields = [
            'uuid',
            'url',
            'name',
            'status',
            'datetime_created',
            'datetime_finished',
            'template',
            'postprocessing_status',
            'status_is_finished',
            'status_is_failed',
            'status_is_killed',
            'status_is_running',
            'status_is_waiting',
            'is_leaf',
            'command',
            'interpreter',
            'environment',
            'resources',
            'notification_addresses',
            'notification_context',
            'user_inputs',
            'inputs',
            'outputs',
            'events',
            'steps',
            'tasks',
            'force_rerun',
        ]

    def validate(self, data):
        if not data.get('uuid'):
            # No extra validation for creating a new run.
            return super(_AbstractWritableRunSerializer, self).validate(data)
        self._preexisting_runs = []
        self._unsaved_runs = []
        self._unsaved_run_outputs = []
        self._unsaved_run_inputs = []
        self._unsaved_run_user_inputs = []
        self._unsaved_run_events = []
        self._run_parent_relationships = []
        self._task_to_task_attempt_relationships = []
        self._task_to_all_task_attempts_m2m_relationships = []
        self._unsaved_tasks = []
        self._unsaved_task_inputs = []
        self._unsaved_task_outputs = []
        self._unsaved_task_events = []
        self._unsaved_task_attempts = []
        self._unsaved_task_attempt_inputs = []
        self._unsaved_task_attempt_outputs = []
        self._unsaved_log_files = []
        self._unsaved_task_attempt_events = []
        # This applies to importing a run record
        try:
            r = Run.objects.get(uuid=data.get('uuid'))
            # If run already exists
            self._root_run_uuid = r.uuid
            self._preexisting_runs.append(r)
            return data
        except Run.DoesNotExist:
            pass

        # Did not find run by UUID. Create a new one.

        self._validate_run_data_fields(self.initial_data)

        run_data = copy.deepcopy(self.initial_data)
        root_run = self._create_unsaved_models([run_data,])
        self._root_run_uuid = root_run.uuid
        for model in self._unsaved_runs:
            try:
                model.full_clean()
            except django.core.exceptions.ValidationError as e:
                raise serializers.ValidationError(e.message_dict)
        return data

    def _validate_run_data_fields(self, run_data):
        data_keys = run_data.keys()
        serializer_keys = self.fields.keys()
        extra_fields = filter(lambda key: key not in serializer_keys, data_keys)
        if extra_fields:
            raise serializers.ValidationError(
                'Unrecognized fields %s' % extra_fields)

    def _create_unsaved_models(
            self,
            runs_data,
            parent_model=None):
        if parent_model:
            parent_force_rerun = parent_model.force_rerun
        else:
            parent_force_rerun = False
        for i in range(len(runs_data)):
            run_data = runs_data[i]
            try:
                run = Run.objects.get(uuid=run_data.get('uuid'))
                self._preexisting_runs.append(run)
            except Run.DoesNotExist:
                run = self._create_unsaved_run(
                    run_data, parent_force_rerun)
            if parent_model:
                self._run_parent_relationships.append((run.uuid, parent_model.uuid))
            children = run_data.get('steps', [])
            has_children = bool(children)
            if has_children:
                # recurse
                self._create_unsaved_models(
                    children,
                    parent_model=run)
        return run

    def _create_unsaved_run(self, run_data, parent_force_rerun):
        self._validate_run_data_fields(run_data)
        run_data.setdefault('force_rerun', parent_force_rerun)
        run_copy = copy.deepcopy(run_data)
        inputs = run_copy.pop('inputs', [])
        user_inputs = run_copy.pop('user_inputs', [])
        outputs = run_copy.pop('outputs', [])
        template_data = run_copy.pop('template')
        tasks = run_copy.pop('tasks', [])
        events = run_copy.pop('events', [])
        run_copy.pop('steps', None)
        run_copy.pop('url', None)
        run_copy.pop('status', None)
        s = TemplateSerializer(data=template_data)
        s.is_valid()
        run_copy['template'] = s.save()
        run = Run(**run_copy)
        self._unsaved_runs.append(run)
        for task in tasks:
            self._create_unsaved_task(task, run)
        for input_data in inputs:
            # create unsaved inputs
            input_copy = copy.deepcopy(input_data)
            input_copy['run'] = run
            data = input_copy.pop('data', None)
            if data:
                s = DataNodeSerializer(
                    data=data,
                    context={'type': input_copy.get('type')}
                )
                s.is_valid(raise_exception=True)
                input_copy['data_node'] = s.save()
            self._unsaved_run_inputs.append(RunInput(**input_copy))
        for user_input in user_inputs:
            # create unsaved user_inputs
            input_copy = copy.deepcopy(user_input)
            input_copy['run'] = run
            data = input_copy.pop('data', None)
            if data:
                s = DataNodeSerializer(
                    data=data,
                    context={'type': input_copy.get('type')}
                )
                s.is_valid(raise_exception=True)
                input_copy['data_node'] = s.save()
            self._unsaved_run_user_inputs.append(UserInput(**input_copy))
        for output_data in outputs:
            # create unsaved outputs
            output_copy = copy.deepcopy(output_data)
            output_copy['run'] = run
            data = output_copy.pop('data', None)
            if data:
                s = DataNodeSerializer(
                    data=data,
                    context={'type': output_copy.get('type')}
                )
                s.is_valid(raise_exception=True)
                output_copy['data_node'] = s.save()
            self._unsaved_run_outputs.append(RunOutput(**output_copy))
        for event in events:
            event['run'] = run
            self._unsaved_run_events.append(RunEvent(**event))
        return run

    def _create_unsaved_task(self, task_data, run):
        task_attempts = task_data.pop('all_task_attempts', [])
        active_task_attempt = task_data.pop('task_attempt', None)
        inputs = task_data.pop('inputs', [])
        outputs = task_data.pop('outputs', [])
        events = task_data.pop('events', [])
        task_data.pop('url', None)
        task_data.pop('status', None)
        task_data['run'] = run
        task = Task(**task_data)
        self._unsaved_tasks.append(task)
        for input_data in inputs:
            # create unsaved inputs
            input_copy = copy.deepcopy(input_data)
            input_copy['task'] = task
            data = input_copy.pop('data', None)
            if data:
                s = DataNodeSerializer(
                    data=data,
                    context={'type': input_copy.get('type')}
                )
                s.is_valid(raise_exception=True)
                input_copy['data_node'] = s.save()
            self._unsaved_task_inputs.append(TaskInput(**input_copy))
        for output_data in outputs:
            output_copy = copy.deepcopy(output_data)
            output_copy['task'] = task
            data = output_copy.pop('data', None)
            if data:
                s = DataNodeSerializer(
                    data=data,
                    context={'type': output_copy.get('type')}
                )
                s.is_valid(raise_exception=True)
                output_copy['data_node'] = s.save()
            self._unsaved_task_outputs.append(TaskOutput(**output_copy))
        for event in events:
            event['task'] = task
            self._unsaved_task_events.append(TaskEvent(**event))
        if active_task_attempt:
            self._task_to_task_attempt_relationships.append(
                (task_data.get('uuid'), active_task_attempt.get('uuid')))
        for task_attempt in task_attempts:
            self._create_unsaved_task_attempt(task_attempt, task)

    def _create_unsaved_task_attempt(self, task_attempt_data, task):
        inputs = task_attempt_data.pop('inputs', [])
        outputs = task_attempt_data.pop('outputs', [])
        events = task_attempt_data.pop('events', [])
        log_files = task_attempt_data.pop('log_files', [])
        task_attempt_data.pop('url', None)
        task_attempt_data.pop('status', None)
        task_attempt = TaskAttempt(**task_attempt_data)
        self._unsaved_task_attempts.append(task_attempt)
        for input_data in inputs:
            input_copy = copy.deepcopy(input_data)
            input_copy['task_attempt'] = task_attempt
            data = input_copy.pop('data', None)
            if data:
                s = DataNodeSerializer(
                    data=data,
                    context={'type': input_copy.get('type')}
                )
                s.is_valid(raise_exception=True)
                input_copy['data_node'] = s.save()
            self._unsaved_task_attempt_inputs.append(TaskAttemptInput(**input_copy))
        for output_data in outputs:
            output_copy = copy.deepcopy(output_data)
            output_copy['task_attempt'] = task_attempt
            data = output_copy.pop('data', None)
            if data:
                s = DataNodeSerializer(
                    data=data,
                    context={'type': output_copy.get('type')}
                )
                s.is_valid(raise_exception=True)
                output_copy['data_node'] = s.save()
            self._unsaved_task_attempt_outputs.append(TaskAttemptOutput(**output_copy))
        for log_file in log_files:
            log_file['task_attempt'] = task_attempt
            data_object = log_file.pop('data_object', None)
            log_file.pop('url')
            if data_object:
                s = DataObjectSerializer(data=data_object)
                s.is_valid(raise_exception=True)
                log_file['data_object'] = s.save()
            log_file = TaskAttemptLogFile(**log_file)
            self._unsaved_log_files.append(log_file)
        for event in events:
            event['task_attempt'] = task_attempt
            self._unsaved_task_attempt_events.append(TaskAttemptEvent(**event))
        self._task_to_all_task_attempts_m2m_relationships.append(
            TaskMembership(parent_task=task, child_task_attempt=task_attempt))

    def create(self, validated_data):
        if validated_data.get('uuid'):
            return self._post_run(validated_data)
        else:
            return self._start_run(validated_data)

    def _post_run(self, data):
        try:
            bulk_runs = Run.objects.bulk_create(self._unsaved_runs)
            self._new_runs = reload_models(Run, bulk_runs)
            all_runs = [run for run in self._new_runs]
            all_runs.extend(self._preexisting_runs)
            match_and_update_by_uuid(self._unsaved_run_inputs, 'run', self._new_runs)
            RunInput.objects.bulk_create(self._unsaved_run_inputs)
            match_and_update_by_uuid(self._unsaved_run_outputs, 'run', self._new_runs)
            RunOutput.objects.bulk_create(self._unsaved_run_outputs)
            match_and_update_by_uuid(self._unsaved_run_user_inputs,
                                     'run', self._new_runs)
            UserInput.objects.bulk_create(self._unsaved_run_user_inputs)
            match_and_update_by_uuid(self._unsaved_run_events, 'run', self._new_runs)
            RunEvent.objects.bulk_create(self._unsaved_run_events)
            match_and_update_by_uuid(self._unsaved_tasks, 'run', self._new_runs)
            bulk_tasks = Task.objects.bulk_create(self._unsaved_tasks)
            self._new_tasks = reload_models(Task, bulk_tasks)
            match_and_update_by_uuid(self._unsaved_task_inputs, 'task', self._new_tasks)
            TaskInput.objects.bulk_create(self._unsaved_task_inputs)
            match_and_update_by_uuid(self._unsaved_task_outputs,
                                     'task', self._new_tasks)
            TaskOutput.objects.bulk_create(self._unsaved_task_outputs)
            match_and_update_by_uuid(self._unsaved_task_events,
                                     'task', self._new_tasks)
            TaskEvent.objects.bulk_create(self._unsaved_task_events)
            bulk_attempts = TaskAttempt.objects.bulk_create(self._unsaved_task_attempts)
            self._new_task_attempts = reload_models(TaskAttempt, bulk_attempts)
            match_and_update_by_uuid(self._unsaved_task_attempt_inputs,
                                     'task_attempt', self._new_task_attempts)
            TaskAttemptInput.objects.bulk_create(self._unsaved_task_attempt_inputs)
            match_and_update_by_uuid(self._unsaved_task_attempt_outputs,
                                     'task_attempt',self._new_task_attempts)
            TaskAttemptOutput.objects.bulk_create(self._unsaved_task_attempt_outputs)
            match_and_update_by_uuid(self._unsaved_task_attempt_events,
                                     'task_attempt', self._new_task_attempts)
            TaskAttemptEvent.objects.bulk_create(self._unsaved_task_attempt_events)
            match_and_update_by_uuid(self._unsaved_log_files,
                                     'task_attempt', self._new_task_attempts)
            TaskAttemptLogFile.objects.bulk_create(self._unsaved_log_files)
            self._connect_tasks_to_active_task_attempts(
                self._new_tasks, self._new_task_attempts)
            match_and_update_by_uuid(
                self._task_to_all_task_attempts_m2m_relationships,
                'parent_task', self._new_tasks)
            match_and_update_by_uuid(
                self._task_to_all_task_attempts_m2m_relationships,
                'child_task_attempt', self._new_task_attempts)
            TaskMembership.objects.bulk_create(
                self._task_to_all_task_attempts_m2m_relationships)
            self._connect_runs_to_parents(all_runs)
            root_run = filter(
                lambda r: r.uuid==self._root_run_uuid, all_runs)
            assert len(root_run) == 1, '1 run should match uuid of root'
            run = root_run[0]
            async.create_fingerprints(run)
            return run
        except Exception as e:
            self._cleanup()
            raise

    def _connect_runs_to_parents(self, runs):
        params = []
        for run_uuid, parent_uuid in self._run_parent_relationships:
            run = filter(
                lambda r: r.uuid==run_uuid, runs)[0]
            parent = filter(
                lambda r: r.uuid==parent_uuid, runs)[0]
            params.append((run.id, parent.id))
        if params:
            case_statement = ' '.join(['WHEN id=%s THEN %s' % pair for pair in params])
            id_list = ', '.join(['%s' % pair[0] for pair in params])
            sql = 'UPDATE api_run SET parent_id= CASE %s END WHERE id IN (%s)' \
                                             % (case_statement, id_list)
            with django.db.connection.cursor() as cursor:
                cursor.execute(sql)

    def _connect_tasks_to_active_task_attempts(self, tasks, task_attempts):
        params = []
        for task_uuid, task_attempt_uuid in self._task_to_task_attempt_relationships:
            task = filter(lambda t: t.uuid==task_uuid, tasks)[0]
            task_attempt = filter(
                lambda ta: ta.uuid==task_attempt_uuid, task_attempts)[0]
            params.append((task.id, task_attempt.id))
        if params:
            case_statement = ' '.join(['WHEN id=%s THEN %s' % pair for pair in params])
            id_list = ', '.join(['%s' % pair[0] for pair in params])
            sql = 'UPDATE api_task SET task_attempt_id= CASE %s END WHERE id IN (%s)' \
                                             % (case_statement, id_list)
            with django.db.connection.cursor() as cursor:
                cursor.execute(sql)

    def _cleanup(self):
        if hasattr(self, '_new_runs'):
            self._new_runs.delete()
        # TODO
        
    def _start_run(self, data):
        user_inputs = self.initial_data.get('user_inputs', None)
        data.pop('user_inputs', None)
        data.pop('template')
        s = TemplateSerializer(data=self.initial_data.get('template'))
        s.is_valid()
        template = s.save()

        run = Run.create_from_template(
            template,
            name=data.get('name'),
            notification_addresses=data.get('notification_addresses'),
            force_rerun=data.get('force_rerun', False),
            notification_context=Run.get_notification_context(
                self.context.get('request')))
        try:
            if user_inputs is not None:
                for input_data in user_inputs:
                    # The user_input usually won't have data type specified.
                    # We need to know the data type to find or create the
                    # data object from the value given. We get the type from the
                    # corresponding template input.
                    if not input_data.get('channel'):
                        raise serializers.ValidationError(
                            'Missing required "channel" field on input: "%s"'
                            % input_data)
                    try:
                        input = template.get_input(input_data.get('channel'))
                    except ObjectDoesNotExist:
                        raise serializers.ValidationError(
                            'Input channel "%s" does not match any channel '\
                            'on the template.' % input_data.get('channel'))
                    if input_data.get('type') and input_data.get('type') != input.type:
                        raise serializers.ValidationError(
                            'Type mismatch: Data with type "%s" does not match '
                            'input channel "%s" with type "%s".' % (
                                input_data.get('type'),
                                input_data.get('channel'), type))
                    input_data.update({'type': input.type})
                    s = UserInputSerializer(
                        data=input_data,
                        context={'parent_field': 'run',
                                 'parent_instance': run
                        })
                    s.is_valid(raise_exception=True)
                    i = s.save()
                    if not i.data_node.is_ready():
                        raise serializers.ValidationError(
                            'Data for input "%s" is not ready. (Maybe a file '\
                            'upload failed or is not yet complete?)' % i.channel)
        except:
            # Cleanup ill-formed run
            run.delete()
            raise

        run.initialize_inputs()
        run.initialize_outputs()
        run.initialize()
        return run

        
class RunSerializer(_AbstractWritableRunSerializer):

    EXPAND = False

    uuid = serializers.UUIDField(required=False)
    url = serializers.HyperlinkedIdentityField(
        view_name='run-detail',
        lookup_field='uuid')
    name = serializers.CharField(required=False)
    datetime_created = serializers.DateTimeField(required=False, format='iso-8601')
    datetime_finished = serializers.DateTimeField(required=False, format='iso-8601')
    template = URLTemplateSerializer(required=False)
    postprocessing_status = serializers.CharField(required=False)
    status = serializers.CharField(read_only=True)
    status_is_finished = serializers.BooleanField(required=False)
    status_is_failed = serializers.BooleanField(required=False)
    status_is_killed = serializers.BooleanField(required=False)
    status_is_running = serializers.BooleanField(required=False)
    status_is_waiting = serializers.BooleanField(required=False)
    is_leaf = serializers.BooleanField(required=False)
    command = serializers.CharField(required=False,
                                    allow_null=True, allow_blank=True)
    interpreter = serializers.CharField(required=False,
                                        allow_null=True, allow_blank=True)
    environment = serializers.JSONField(required=False, allow_null=True)
    resources = serializers.JSONField(required=False, allow_null=True)
    notification_addresses = serializers.JSONField(required=False, allow_null=True)
    notification_context = serializers.JSONField(required=False, allow_null=True)
    user_inputs = UserInputSerializer(many=True, required=False)
    inputs = RunInputSerializer(many=True, required=False)
    outputs = RunOutputSerializer(many=True, required=False)
    events = RunEventSerializer(many=True, required=False)
    steps = RecursiveField(many=True, required=False)
    tasks = TaskSerializer(many=True, required=False)
    force_rerun = serializers.BooleanField(required=False, write_only=True)
    
    def to_representation(self, instance):
        if not hasattr(instance, '_prefetched_objects_cache'):
            self._prefetch_instance(instance)
        return strip_empty_values(
            super(RunSerializer, self).to_representation(instance))

    def _prefetch_instance(self, instance):
        queryset = Run\
                   .objects\
                   .filter(uuid=instance.uuid)\
                   .prefetch_related('steps')\
                   .prefetch_related('steps__steps')\
                   .prefetch_related('steps__steps__steps')\
                   .prefetch_related('steps__steps__steps__steps')\
                   .prefetch_related('steps__steps__steps__steps__steps')\
                   .prefetch_related('steps__steps__steps__steps__steps__'\
                                     'steps')\
                   .prefetch_related('steps__steps__steps__steps__steps__'\
                                     'steps__steps')\
                   .prefetch_related('steps__steps__steps__steps__steps__'\
                                     'steps__steps__steps')\
                   .prefetch_related('steps__steps__steps__steps__steps__'\
                                     'steps__steps__steps__steps')\
                   .prefetch_related('steps__steps__steps__steps__steps__'\
                                     'steps__steps__steps__steps__steps')
        instance._prefetched_objects_cache = queryset[0]._prefetched_objects_cache
        node_list = flatten_nodes(instance, 'steps')
        queryset = Run.objects.filter(uuid__in=[n.uuid for n in node_list])\
            .prefetch_related('inputs')\
            .prefetch_related('inputs__data_node')\
            .prefetch_related('outputs')\
            .prefetch_related('outputs__data_node')\
            .prefetch_related('user_inputs')\
            .prefetch_related('user_inputs__data_node')\
            .prefetch_related('template')\
            .prefetch_related('events')\
            .prefetch_related('tasks')\
            .prefetch_related('tasks__inputs')\
            .prefetch_related('tasks__inputs__data_node')\
            .prefetch_related('tasks__outputs')\
            .prefetch_related('tasks__outputs__data_node')\
            .prefetch_related('tasks__events')\
            .prefetch_related('tasks__all_task_attempts')\
            .prefetch_related('tasks__all_task_attempts__inputs')\
            .prefetch_related('tasks__all_task_attempts__inputs__data_node')\
            .prefetch_related('tasks__all_task_attempts__outputs')\
            .prefetch_related('tasks__all_task_attempts__outputs__data_node')\
            .prefetch_related('tasks__all_task_attempts__events')\
            .prefetch_related('tasks__all_task_attempts__log_files')\
            .prefetch_related('tasks__all_task_attempts__log_files__data_object')\
            .prefetch_related(
                'tasks__all_task_attempts__log_files__data_object__file_resource')\
            .prefetch_related('tasks__task_attempt')\
            .prefetch_related('tasks__task_attempt__inputs')\
            .prefetch_related('tasks__task_attempt__inputs__data_node')\
            .prefetch_related('tasks__task_attempt__outputs')\
            .prefetch_related('tasks__task_attempt__outputs__data_node')\
            .prefetch_related('tasks__task_attempt__events')\
            .prefetch_related('tasks__task_attempt__log_files')\
            .prefetch_related('tasks__task_attempt__log_files__data_object')\
            .prefetch_related(
                'tasks__task_attempt__log_files__data_object__file_resource')
        runs = [run for run in queryset]
        data_nodes = []
	for run in runs:
            for input in run._prefetched_objects_cache.get('inputs', []):
                data_node = input.data_node
                if data_node:
                    data_nodes.append(data_node)
            for user_input in run._prefetched_objects_cache.get('user_inputs', []):
                data_node = user_input.data_node
                if data_node:
                    data_nodes.append(data_node)
            for output in run._prefetched_objects_cache.get('outputs', []):
                data_node = output.data_node
                if data_node:
                    data_nodes.append(data_node)
            for task in run._prefetched_objects_cache.get('tasks', []):
                for input in task._prefetched_objects_cache.get('inputs', []):
                    data_node = input.data_node
                    if data_node:
                        data_nodes.append(data_node)
                for output in task._prefetched_objects_cache.get('outputs', []):
                    data_node = output.data_node
                    if data_node:
                        data_nodes.append(data_node)
                for task_attempt in task._prefetched_objects_cache.get(
                        'all_task_attempts', []):
                    for input in task_attempt._prefetched_objects_cache.get(
                            'inputs', []):
                        data_node = input.data_node
                        if data_node:
                            data_nodes.append(data_node)
                    for output in task_attempt._prefetched_objects_cache.get(
                            'outputs', []):
                        data_node = output.data_node
                        if data_node:
                            data_nodes.append(data_node)
                if task.task_attempt:
                    for input in task.task_attempt._prefetched_objects_cache.get(
                            'inputs', []):
                        data_node = input.data_node
                        if data_node:
                            data_nodes.append(data_node)
                    for output in task.task_attempt._prefetched_objects_cache.get(
                            'outputs', []):
                        data_node = output.data_node
                        if data_node:
                            data_nodes.append(data_node)
        replace_nodes(instance, runs, 'steps', ['template',])
	if self.EXPAND:
            ExpandedDataNodeSerializer.prefetch_instances(data_nodes)
        else:
            DataNodeSerializer.prefetch_instances(data_nodes)


class ExpandedRunSerializer(RunSerializer):

    EXPAND = True

    user_inputs = ExpandedUserInputSerializer(many=True, required=False)
    inputs = ExpandedRunInputSerializer(many=True, required=False)
    outputs = ExpandedRunOutputSerializer(many=True, required=False)
    tasks = ExpandedTaskSerializer(many=True, required=False)


class URLRunSerializer(_AbstractWritableRunSerializer):

    # readable fields
    uuid = serializers.UUIDField(required=False)
    url = serializers.HyperlinkedIdentityField(
        view_name='run-detail',
        lookup_field='uuid')
    name = serializers.CharField(required=False)
    datetime_created = serializers.DateTimeField(
        required=False, format='iso-8601')
    datetime_finished = serializers.DateTimeField(
        required=False, format='iso-8601')
    status = serializers.CharField(read_only=True)
    is_leaf = serializers.BooleanField(required=False)

    # write-only fields
    template = URLTemplateSerializer(required=False, write_only=True)
    postprocessing_status = serializers.CharField(required=False, write_only=True)
    status_is_finished = serializers.BooleanField(required=False, write_only=True)
    status_is_failed = serializers.BooleanField(required=False, write_only=True)
    status_is_killed = serializers.BooleanField(required=False, write_only=True)
    status_is_running = serializers.BooleanField(required=False, write_only=True)
    status_is_waiting = serializers.BooleanField(required=False, write_only=True)
    command = serializers.CharField(required=False, write_only=True)
    interpreter = serializers.CharField(required=False, write_only=True)
    environment = serializers.JSONField(required=False, write_only=True)
    resources = serializers.JSONField(required=False, write_only=True)
    notification_addresses = serializers.JSONField(
        required=False, write_only=True, allow_null=True)
    notification_context = serializers.JSONField(
        required=False, write_only=True, allow_null=True)
    user_inputs = UserInputSerializer(
        many=True, required=False, write_only=True)
    inputs = RunInputSerializer(many=True, required=False, write_only=True)
    outputs = RunOutputSerializer(many=True, required=False, write_only=True)
    events = RunEventSerializer(many=True, required=False, write_only=True)
    steps = RecursiveField(many=True, required=False, write_only=True)
    tasks = TaskSerializer(many=True, required=False, write_only=True)
    force_rerun = serializers.BooleanField(required=False, write_only=True)
