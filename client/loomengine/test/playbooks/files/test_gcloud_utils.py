import os
import sys
import unittest

playbook_files_path = os.path.abspath(
    os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)),
        '..','..','..','playbooks','files'))

sys.path.append(playbook_files_path)

import gcloud_utils as gu

class TestGcloudUtils(unittest.TestCase):

    def testGetWorkerName(self):
        hostname = 'host'
        step_name = 'step'
        attempt_id = '123'
        max_length = 63
        worker_name = gu.get_worker_name(hostname, step_name, attempt_id, max_length)
        self.assertEqual(worker_name, '%s-%s-%s' % (hostname, step_name, attempt_id))

    def testGetWorkerNameTrimEven(self):
        hostname = 'hostname'
        step_name = 'stepname'
        attempt_id = '12345678910'
        max_length = 6+6+8+2
        worker_name = gu.get_worker_name(hostname, step_name, attempt_id, max_length)
        self.assertEqual(worker_name, 'hostna-stepna-12345678')

    def testGetWorkerNameTrimOdd(self):
        hostname = 'hostname'
        step_name = 'stepname'
        attempt_id = '12345678910'
        max_length = 6+5+8+2
        worker_name = gu.get_worker_name(hostname, step_name, attempt_id, max_length)
        self.assertEqual(worker_name, 'hostna-stepn-12345678')

    def testGetScratchDiskName(self):
        hostname = 'host'
        step_name = 'step'
        attempt_id = '123'
        max_length = 63
        disk_name = gu.get_scratch_disk_name(hostname, step_name, attempt_id, max_length)
        self.assertEqual(disk_name, '%s-%s-%s-disk' % (hostname, step_name, attempt_id))

    def testSanitizeInstanceName(self):
        name = gu._sanitize_instance_name('--some_?&-things-nevr-change--', 100)
        self.assertEqual(name, 'some-things-nevr-change')
    
    def testSanitizeServerName(self):
        name = gu.sanitize_server_name('--some_?&-things-nevr-change--', 10)
        self.assertEqual(name, 'some-things-nevr-change'[:10])


if __name__=='__main__':
    unittest.main()
