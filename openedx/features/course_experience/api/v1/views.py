from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.exceptions import APIException, ParseError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import RetrieveAPIView

from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.auth.session.authentication import SessionAuthenticationAllowInactiveUser

from lms.djangoapps.courseware.courses import get_course_with_access

from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.schedules.utils import reset_self_paced_schedule
from openedx.core.lib.api.authentication import BearerAuthenticationAllowInactiveUser
from openedx.features.course_experience.api.v1.serializers import CourseDeadlinesMobileSerializer


class UnableToResetDeadlines(APIException):
    status_code = 400
    default_detail = 'Unable to reset deadlines.'
    default_code = 'unable_to_reset_deadlines'


@api_view(['POST'])
@authentication_classes((
    JwtAuthentication, BearerAuthenticationAllowInactiveUser, SessionAuthenticationAllowInactiveUser,
))
@permission_classes((IsAuthenticated,))
def reset_course_deadlines(request):
    course_key = request.data.get('course_key', None)

    # If body doesnt contain 'course_key', return 400 to client.
    if not course_key:
        raise ParseError("'course_key' is required.")

    # If body contains params other than 'course_key', return 400 to client.
    if len(request.data) > 1:
        raise ParseError("Only 'course_key' is expected.")

    try:
        reset_self_paced_schedule(request.user, course_key)
        return Response({'message': 'Deadlines successfully reset.'})
    except Exception:
        raise UnableToResetDeadlines


class CourseDeadlinesMobileView(RetrieveAPIView):
    """
    **Use Cases**

        Request course deadline info for mobile

    **Example Requests**

        GET api/course_experience/v1/course_deadlines_info/{course_key}

    **Response Values**

        Body consists of the following fields:

        dates_banner_info: (obj)
            missed_deadlines: (bool) Whether the user has missed any graded content deadlines for the given course.
            missed_gated_content: (bool) Whether the user has missed any gated content for the given course.
            content_type_gating_enabled: (bool) Whether content type gating is enabled for this enrollment.
            verified_upgrade_link: (str) The URL to ecommerce IDA for purchasing the verified upgrade.

    **Returns**

        * 200 on success with above fields.
        * 401 if the user is not authenticated.
        * 404 if the course is not available or cannot be seen.
    """

    authentication_classes = (
        JwtAuthentication,
        BearerAuthenticationAllowInactiveUser,
        SessionAuthenticationAllowInactiveUser,
    )
    permission_classes = (IsAuthenticated,)
    serializer_class = CourseDeadlinesMobileSerializer

    def get(self, request, *args, **kwargs):
        course_key_string = kwargs.get('course_key_string')
        course_key = CourseKey.from_string(course_key_string)
        get_course_with_access(request.user, 'load', course_key)

        serializer = self.get_serializer({})
        return Response(serializer.data)
