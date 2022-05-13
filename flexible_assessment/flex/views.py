import pprint

from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST
from pylti1p3.contrib.django import DjangoMessageLaunch, DjangoOIDCLogin
from django.contrib.auth.decorators import login_required

import flex.models as models
import flex.utils as utils


def index(request):
    return HttpResponse('Home page')


def login(request):
    tool_conf = utils.get_tool_conf()
    launch_data_storage = utils.get_launch_data_storage()
    pprint.pprint(request)

    oidc_login = DjangoOIDCLogin(
        request,
        tool_conf,
        launch_data_storage=launch_data_storage)
    target_link_uri = utils.get_launch_url(request)
    return oidc_login.enable_check_cookies().redirect(target_link_uri)


@require_POST
def launch(request):
    tool_conf = utils.get_tool_conf()
    launch_data_storage = utils.get_launch_data_storage()
    message_launch = DjangoMessageLaunch(
        request, tool_conf, launch_data_storage=launch_data_storage)
    message_launch_data = message_launch.get_launch_data()
    pprint.pprint(message_launch_data)

    custom_fields = message_launch_data['https://purl.imsglobal.org/spec/lti/claim/custom']

    utils.add_permissions()

    # TODO: TAEnrollement view
    if 'TeacherEnrollment' in custom_fields['role']:
        utils.set_user_course(request, custom_fields, models.Roles.TEACHER)
        utils.authenticate_login(request)
        return HttpResponseRedirect(reverse('flex:instructor_view'))

    elif 'StudentEnrollment' in custom_fields['role']:
        utils.set_user_course(request, custom_fields, models.Roles.STUDENT)
        utils.authenticate_login(request)
        return HttpResponseRedirect(reverse('flex:student_view'))


def get_jwks(request):
    tool_conf = utils.get_tool_conf()
    return JsonResponse(tool_conf.get_jwks(), safe=False)


@login_required
def instuctor(request):
    response_string = 'Instructor Page, your user id: {} and name: {}'
    user_id = request.session.get('user_id', '')
    display_name = request.session.get('display_name', '')
    if not user_id:
        raise Http404

    return HttpResponse(response_string.format(user_id, display_name))


@login_required
def student(request):
    response_string = 'Student Page, your user id: {} and name: {}'
    user_id = request.session.get('user_id', '')
    display_name = request.session.get('display_name', '')
    if not user_id:
        raise Http404

    return HttpResponse(response_string.format(user_id, display_name))
