import logging
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from analysis.models import File, RequestSubmission, WorkInProgress, StepRun, StepResult

logger = logging.getLogger('loom')

class Helper:

    @classmethod
    def create(cls, request, model_class):
        data_json = request.body
        try:
            model = model_class.create(data_json)
            return JsonResponse({"message": "created %s" % model_class.get_name(), "_id": str(model._id)}, status=201)
        except Exception as e:
            return JsonResponse({"message": e.message}, status=400)

    @classmethod
    def index(cls, request, model_class):
        model_list = []
        for model in model_class.objects.all():
            model_list.append(model.downcast().to_serializable_obj())
        return JsonResponse({model_class.get_name(plural=True): model_list}, status=200)

    @classmethod
    def show(cls, request, id, model_class):
        model = model_class.get_by_id(id)
        return JsonResponse(model.to_serializable_obj(), status=200)

    @classmethod
    def update(cls, request, id, model_class):
        model = model_class.get_by_id(id)
        data_json = request.body
        try:
            model.update(data_json)
            return JsonResponse({"message": "updated %s _id=%s" % (model_class.get_name(), model._id)}, status=201)
        except Exception as e:
            return JsonResponse({"message": e.message}, status=400)

@require_http_methods(["GET"])
def status(request):
    return JsonResponse({"message": "server is up"}, status=200)

@require_http_methods(["GET"])
def workerinfo(request):
    workerinfo = {
        'FILE_SERVER_FOR_WORKER': settings.FILE_SERVER_FOR_WORKER,
        'FILE_ROOT': settings.FILE_ROOT,
        'WORKER_LOGFILE': settings.WORKER_LOGFILE,
        'LOG_LEVEL': settings.LOG_LEVEL,
        }
    return JsonResponse({'workerinfo': workerinfo})

@csrf_exempt
@require_http_methods(["POST"])
def submitrequest(request):
    data_json = request.body
    try:
        request_submission = RequestSubmission.create(data_json)
        logger.info('Created request submission %s' % request_submission._id)
    except Exception as e:
        logger.error('Failed to create request submission with data "%s". %s' % (data_json, e.message))
        return JsonResponse({"message": e.message}, status=400)
    try:
        WorkInProgress.submit_new_request(request_submission.to_obj())
        return JsonResponse({"message": "created new %s" % request_submission.get_name(), "_id": str(request_submission._id)}, status=201)
    except Exception as e:
        return JsonResponse({"message": e.message}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def submitresult(request):
    data_json = request.body
    try:
        result = WorkInProgress.submit_result(data_json)
        return JsonResponse({"message": "created new %s" % result.get_name(), "_id": str(result._id)}, status=201)
    except Exception as e:
        return JsonResponse({"message": e.message}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def closerun(request):
    data_json = request.body
    try:
        WorkInProgress.close_run(data_json)
        return JsonResponse({"message": "closed run", "_id": data_json.get('_id')})
    except Exception as e:
        return JsonResponse({"message": e.message}, status=500)
    run_id = data_json.get('_id')

@csrf_exempt
@require_http_methods(["GET", "POST"])
def create_or_index(request, model_class):
    if request.method == "POST":
        return Helper.create(request, model_class)
    else:
        return Helper.index(request, model_class)
   
@csrf_exempt
@require_http_methods(["GET", "POST"])
def show_or_update(request, id, model_class):
    if request.method == "POST":
        return Helper.update(request, id, model_class)
    else:
        return Helper.show(request, id, model_class)

@csrf_exempt
@require_http_methods(["GET"])
def show_input_port_bundles(request, id):
    step_run = StepRun.get_by_id(id)
    input_port_bundles = step_run.get_input_port_bundles()
    return JsonResponse({"input_port_bundles": input_port_bundles}, status=200)

@csrf_exempt
@require_http_methods(["GET"])
def dashboard(request):
    # Display all active RequestSubmissions plus the last n closed RequestSubmissions

    def get_count(request):
        DEFAULT_COUNT_STR = '10'
        count_str = request.GET.get('count', DEFAULT_COUNT_STR)
        try:
            count = int(count_str)
        except ValueError as e:
            count = int(DEFAULT_COUNT_STR)
        if count < 0:
            count = int(DEFAULT_COUNT_STR)
        return count

    def get_step_info(s):
        return {
            'id': s.get_field_as_serializable('_id'),
            'name': s.name,
            'is_complete': s.is_complete(),
            'command': s.command,
            }

    def get_workflow_info(w):
        return {
            'id': w.get_field_as_serializable('_id'),
            'name': w.name,
            'is_complete': w.is_complete(),
            'steps': [
                get_step_info(s) for s in w.steps.order_by('datetime_created').reverse().all()
                ]
            }

    def get_request_submission_info(r):
        return {
            'created_at': r.datetime_created,
            'is_complete': r.is_complete(),
            'id': r.get_field_as_serializable('_id'),
            'workflows': [ 
                get_workflow_info(w) for w in r.workflows.order_by('datetime_created').reverse().all()
                ]
            }

    count = get_count(request)
    request_submissions = RequestSubmission.get_sorted(count=count)
    if len(request_submissions) == 0:
        request_submissions_info = []
    request_submissions_info = [get_request_submission_info(r) for r in request_submissions]

    return JsonResponse({'request_submissions': request_submissions_info}, status=200)
