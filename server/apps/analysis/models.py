'''
database model definitions for an analysis
an analysis is of a pipeline with 1-n sessions which could be running in different environment.
a Session is of several analyzing steps
a Session own its own inputs/outputs which are shared by the analyzing steps within this session.
a File is a URL pointing to persistance location of the data, could be a file path or internet URL and etc

a database entry will be generated automatically by parsing json input, by calling jsonToClass
'''

import json
import copy
from django.db import models
from django.core import serializers
from datetime import datetime
from datetime import timedelta

class File(models.Model):
    fileid = models.CharField(primary_key=True, max_length=30)
    uri = models.CharField(max_length=256)
    ownerid = models.IntegerField(default=0)
    access = models.IntegerField(default=755)
    comment = models.CharField(max_length=256, default='')
    def jsonToClass( self, aux ):
        self.fileid = aux['id']
        self.uri = aux['path']
        self.comment = aux['comment']


class Resource(models.Model):
    resourceid = models.IntegerField(primary_key=True, default=0)
    diskspace = models.IntegerField(default=1000)
    memory = models.IntegerField(default=1000)
    cores = models.IntegerField(default=1)
    ownerid = models.IntegerField(default=0)
    access = models.IntegerField(default=755)
    comment = models.CharField(max_length=256, default='')
    def jsonToClass( self, aux ):
        self.resourceid = aux['id']
        self.diskspace = aux['disk_space']
        self.memory = aux['disk_space']
        self.cores = aux['cores']

class Step(models.Model):
    stepid = models.CharField(primary_key=True, max_length=256)
    stepname = models.CharField(max_length=30)
    cmd = models.CharField(max_length=256)
    application = models.CharField(max_length=256)
    comment = models.CharField(max_length=256, default='')
    access = models.IntegerField(default=755)
    def jsonToClass( self, aux ):
        self.stepid = aux['id']
        self.comment = aux['comment']
        self.cmd = aux['command']
        self.application = aux['application']
        

class Session(models.Model):
    sessionid = models.CharField(primary_key=True, max_length=256)
    sessionname = models.CharField(max_length=30)
    steps = models.ManyToManyField(Step, related_name = 'step_id')
    importfiles = models.ManyToManyField(File, related_name = 'infile_id')
    savefiles = models.ManyToManyField(File, related_name = 'outfile_id')
    resourceid = models.ForeignKey(Resource, null=True, blank=True)
    comment = models.CharField(max_length=256, default='')
    access = models.IntegerField(default=755)
    def jsonToClass( self, aux ):
        self.sessionid = aux['id']
        self.comment = aux['comment']
    

class Pipeline(models.Model):
    pipelineid = models.CharField(primary_key=True, max_length=256)
    pipelinename = models.CharField(max_length=30)
    sessionids = models.ManyToManyField(Session, related_name = "session_id")
    comment = models.CharField(max_length=256, default='')
    access = models.IntegerField(default=755)
    def jsonToClass( self, query ):
        # files
        file_dict = {'':''}
        if type(query["files"]) is list :
            for file_entry in query["files"]:
                        f = File(uri="", fileid="", ownerid=0, comment="")
                        f.jsonToClass(file_entry)
                        f.save()
                        file_dict[file_entry["id"]]=f

            # steps
            step_dict = {'':''}
            if type(query["steps"]) is list :
                for step_entry in query["steps"]:
                        s = Step(stepid="")
                        s.jsonToClass( step_entry )
                        s.save()
                        step_dict[step_entry['id']] = s
            
            # sessions
            if type(query["sessions"]) is list :
                for session_entry in query["sessions"]:
                        s = Session(sessionid="", sessionname="", comment="")
                        s.jsonToClass( session_entry )
                        #init foreign keys
                        s.pipelineid = self
                        s.save()
                        for item in session_entry["input_file_ids"]:
                            s.importfiles.add(file_dict[item])
                        for item in session_entry["output_file_ids"]:
                            s.savefiles.add(file_dict[item])
                        for item in session_entry["step_ids"]:
                            s.steps.add(step_dict[item])
                        s.save()
                        self.save()
                        self.sessionids.add(s)


class Analysis(models.Model):
    analysisid = models.CharField(primary_key=True, max_length=256)
    pipelineid = models.ForeignKey(Pipeline, null=False)
    comment = models.CharField(max_length=256)
    ownerid = models.IntegerField(default=0)
    access = models.IntegerField(default=755)
    def prepareJSON(self):
        objs_4_runner = []
        import_file_objs = []
        export_file_objs = []
        step_objs = []
        for session in self.pipelineid.sessionids.all():
            for file_entry in session.importfiles.all():
                obj_4_runner = {}
                obj_4_runner['input_file_ids']=file_entry.uri
                import_file_objs.append(obj_4_runner)
            for file_entry in session.savefiles.all():
                obj_4_runner = {}
                obj_4_runner['output_file_ids']=file_entry.uri
                export_file_objs.append(obj_4_runner)
            for step in session.steps.all():
                obj_4_runner = {}
                obj_4_runner['container']=step.application
                obj_4_runner['command']=step.cmd
                step_objs.append(obj_4_runner)
        objs_4_runner.append({'files':{'imports':import_file_objs,'exports':export_file_objs}})
        objs_4_runner.append({'steps':step_objs})
        return json.dumps(objs_4_runner)


class AnalysisStatus(models.Model):
    statusid = models.CharField(max_length=256, primary_key=True)
    analysis = models.ForeignKey(Analysis, null=True)
    server = models.CharField(max_length=256, default="localhost")
    starttime = models.DateTimeField(default=datetime.now())
    endtime = models.DateTimeField(default=datetime.now())
    retries = models.IntegerField(default=0)
    ramusage = models.IntegerField(default=0)
    coresusage = models.IntegerField(default=1)
    status = models.IntegerField(default=0) #0x0:new, 0x1:running, 0x2:done 
    msg = models.CharField(max_length=256)
    def updateStatus(self, query):
        if 'server' in query: 
            self.server = query['server']
        if 'starttime' in query: 
            self.starttime = query['starttime']
        if 'endtime' in query: 
            self.endtime = query['endtime']
        if 'retries' in query: 
            self.retries = query['retries']
        if 'ramusage' in query: 
            self.ramusage= query['ramusage']
        if 'coreusage' in query: 
            self.coresusage = query['coresusage']
        if 'msg' in query: 
            self.msg = query['msg']
        self.save()



