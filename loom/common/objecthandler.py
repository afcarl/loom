import json
import requests
from loom.common.exceptions import *

class ObjectHandler(object):
    """ObjectHandler provides functions to create and work with objects in the 
    Loom database via the HTTP API
    """

    def __init__(self, master_url):
        self.api_root_url = master_url + '/api/'

    # ---- General methods ----
    
    def _post(self, data, relative_url, raise_for_status=False):
        url = self.api_root_url + relative_url
        return self._make_request_to_server(lambda: requests.post(url, data=json.dumps(data)), raise_for_status=raise_for_status)

    def _get(self, relative_url, raise_for_status=False):
        url = self.api_root_url + relative_url
        return self._make_request_to_server(lambda: requests.get(url), raise_for_status=raise_for_status)
    
    def _make_request_to_server(self, query_function, raise_for_status=False):
        """Verifies server connection and handles response errors
        for either get or post requests
        """
        try:
            response = query_function()
        except requests.exceptions.ConnectionError as e:
            raise ServerConnectionError("No response from server.\n%s" % (url, e))
        if raise_for_status:
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                raise BadResponseError("%s\n%s" % (e.message, response.text))
        return response

    def _post_object(self, object_data, relative_url):
        return self._post(object_data, relative_url, raise_for_status=True).json()['object']

    def _get_object(self, relative_url, raise_for_status=False):
        response = self._get(relative_url)
        if response.status_code == 404:
            return None
        elif response.status_code == 200:
            return response.json()
        else:
            raise BadResponseError("Status code %s.\n%s" % response.status_code)

    def get_server_time(self):
        """Use this, not local system time,  when generating a time stamp in the client
        """
        response = self._get('servertime/')
        return response.json()['time']

    # ---- Post/Get [object_type] methods ----
    
    def get_data_object_array(self, array_id):
        return self._get_object(
            'data_object_arrays/'+array_id
        )

    def post_data_object_array(self, data_object_array):
        return self._post_object(
            data_object_array,
            'data_object_arrays/')

    def get_file_data_object(self, file_id):
        return self._get_object(
            'file_data_objects/'+file_id
        )

    def post_file_data_object(self, file_data_object):
        return self._post_object(
            file_data_object,
            'file_data_objects/') 

    def get_file_or_array_by_id(self, file_id):
        file_data_object = self.get_file_data_object(file_id)
        if file_data_object is not None:
            return [file_data_object]
        else:
            # Not a file. See if it is an array.
            data_object_array = self.get_data_object_array(file_id)
            if data_object_array is None:
                raise ObjectNotFoundError("Could not find file or file array with ID %s" % file_id)
            file_data_objects = data_object_array['data_objects']
            # Arrays can be of any type. Verify that these are files.
            if not all([o.get('file_contents') for o in data_object_array['data_objects']]):
                raise ObjectNotFoundError("Could not find file or file array with ID %s" % file_id)
            return file_data_objects

    def get_file_storage_locations_by_file(self, file_id):
        return self._get_object(
            'file_data_objects/'+file_id+'/file_storage_locations/'
        )['file_storage_locations']

    def post_file_storage_location(self, file_storage_location):
        return self._post_object(
            file_storage_location,
            'file_storage_locations/')

    def post_data_source_record(self, data_source_record):
        return self._post_object(
            data_source_record,
            'data_source_records/'
        )

    def get_workflow(self, workflow_id):
        return self._get_object(
            'workflows/'+workflow_id
        )
    
    def post_workflow(self, workflow):
        return self._post_object(
            workflow,
            'workflows/')

    def get_workflow_run_request(self, workflow_run_request_id):
        return self._get_object(
            'workflow_run_requestss/'+workflow_run_request_id
        )
        
    def post_workflow_run_request(self, workflow_run_request):
        return self._post_object(
            workflow_run_request,
            'workflow_run_requests/')
