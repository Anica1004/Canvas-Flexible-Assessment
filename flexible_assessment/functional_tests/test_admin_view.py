from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from flexible_assessment.models import UserProfile
from django.urls import reverse
from student.views import StudentHome, StudentAssessmentView
from django.test import Client, tag
import time
from flexible_assessment.tests.test_data import DATA
from flexible_assessment.tests.mock_classes import *
from unittest.mock import patch

class TestStudentViews(StaticLiveServerTestCase):
    fixtures = DATA
        
    def setUp(self):
        self.browser =  webdriver.Chrome("functional_tests/chromedriver.exe")
        user = UserProfile.objects.get(login_id="admin")
        self.client = Client()
        self.client.force_login(user)
        
    def tearDown(self):
        self.browser.close()
    
    @tag('slow', 'view')
    @patch("instructor.views.FlexCanvas", return_value=MockFlexCanvas)
    def test_start(self, mock_flex_canvas):
        session_id = self.client.session.session_key
        self.client.session['display_name'] = "HEllo"
        self.browser.get(self.live_server_url + reverse('instructor:instructor_home', args=[1])) 
        self.browser.add_cookie({'name': 'sessionid', 'value': session_id})
        self.browser.add_cookie({'name': 'display_name', 'value': "TEST"})

        self.browser.get(self.live_server_url + reverse('instructor:instructor_home', args=[1])) 
        
        time.sleep(500)
    