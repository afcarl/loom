from django.test import TestCase

from api.models import *
from api.test import fixtures


class TestTaskRunAttempt(TestCase):

    def test_post_save(self):
        step = Step.objects.create(command='blank')
        step_run = StepRun.objects.create(template=step)
        task_run = TaskRun.objects.create(step_run=step_run)

        task_run_attempt = TaskRunAttempt.objects.create(task_run=task_run)
        task_run_attempt._post_save()

        # Worker Process should be automatically created
        self.assertIsNotNone(task_run_attempt.worker_process)

        # Its status should be 'not_started'
        self.assertEqual(task_run_attempt.worker_process.status, 'not_started')
        
