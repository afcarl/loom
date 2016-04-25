'use strict';

angular
    .module('loom.services')
    .service('DataService', DataService)

DataService.$inject = ['$http'];

function DataService($http) {
    /* DataService retrieves and caches data from the server. */
    
    this.setActiveStepRun = setActiveStepRun;
    this.setActiveWorkflow = setActiveWorkflow;
    this.setActiveStep = setActiveStep;
    this.setActiveRun = setActiveRun;
    this.setActiveFile = setActiveFile;
    this.setActiveFileSourceRecords = setActiveFileSourceRecords;
    this.setActiveFileSourceRuns = setActiveFileSourceRuns;
    this.setActiveFileStorageLocations = setActiveFileStorageLocations;
    this.getActiveData = getActiveData;
    this.getRuns = getRuns;    
    this.getWorkflows = getWorkflows;
    this.getFiles = getFiles;

    var activeData = {};
    
    function getActiveData() {
	return activeData;
    };

    function setActiveRun(runId) {
	return $http.get('/api/workflow_runs/' + runId + '/')
            .then(function(response) {
		activeData.run = response.data;
            });
    };

    function setActiveStepRun(stepRunId) {
	return $http.get('/api/step_runs/' + stepRunId + '/')
            .then(function(response) {
		activeData.stepRun = response.data;
            });
    };

    function setActiveWorkflow(workflowId) {
	return $http.get('/api/workflows/' + workflowId + '/')
            .then(function(response) {
		activeData.workflow = response.data;
            });
    };

    function setActiveStep(stepId) {
	return $http.get('/api/steps/' + stepId + '/')
            .then(function(response) {
		activeData.step = response.data;
            });
    };

    function setActiveFile(fileId) {
	return $http.get('/api/file_data_objects/' + fileId + '/')
            .then(function(response) {
		activeData.file = response.data;
            });
    };
    
    function setActiveFileSourceRuns(fileId) {
	return $http.get('/api/file_data_objects/' + fileId + '/source_runs/')
	    .then(function(response) {
		activeData.fileSourceRuns = response.data.runs;
	    });
    };

    function setActiveFileSourceRecords(fileId) {
	return $http.get('/api/file_data_objects/' + fileId + '/data_source_records/')
	    .then(function(response) {
		activeData.fileSourceRecords = response.data.data_source_records;
	    });
    };

    function setActiveFileStorageLocations(fileId) {
	return $http.get('/api/file_data_objects/' + fileId + '/file_storage_locations/')
	    .then(function(response) {
		activeData.fileStorageLocations = response.data.file_storage_locations;
	    });
    };

    function getRuns() {
	return $http.get('/api/workflow_runs/')
	    .then(function(response) {
		return response.data.workflow_runs;
	    });
    };

    function getWorkflows() {
	return $http.get('/api/workflows/')
	    .then(function(response) {
		return response.data.workflows;
	    });
    };

    function getFiles() {
	return $http.get('/api/file_data_objects/')
	    .then(function(response) {
		return response.data.file_data_objects;
	    });
    };
};
