from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select, WebDriverWait
import flexible_assessment.models as models
from django.urls import reverse
from django.test import Client, tag
from django.http import HttpResponseRedirect
from datetime import datetime, timedelta
from flexible_assessment.tests.test_data import DATA
from unittest.mock import patch, MagicMock, ANY

import flexible_assessment.tests.mock_classes as mock_classes

class TestStudentViews(StaticLiveServerTestCase):
    fixtures = DATA
        
    def setUp(self):
        self.browser =  webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
        user = models.UserProfile.objects.get(login_id="test_instructor1")
        self.client = Client()
        self.client.force_login(user)
        self.launch_url = reverse('launch')
        self.login_url = reverse('login')

    def tearDown(self):
        self.browser.close()
    
    def launch_new_user(self, course_data):
        client = Client()
        launch_data = {'https://purl.imsglobal.org/spec/lti/claim/custom': course_data}

        message_launch_instance = MagicMock()
        message_launch_instance.get_launch_data.return_value = launch_data
        
        with patch('flexible_assessment.lti.get_tool_conf') as mock_get_tool_conf, \
                patch('flexible_assessment.views.DjangoMessageLaunch', return_value=message_launch_instance), \
                patch('flexible_assessment.models.Course.objects.get') as mock_course_get:

                response = client.post(reverse('launch'))
        
        session_id = client.session.session_key
        browser = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install())) 
        browser.get(self.live_server_url + response.url)        
        browser.add_cookie({'name': 'sessionid', 'value': session_id})
        browser.get(self.live_server_url + response.url)
        return browser
    
    @tag('slow')
    def test_login_and_launch_success(self):
        # Mock the lti module functions used in the login view
        with patch('flexible_assessment.lti.get_tool_conf') as mock_get_tool_conf, \
                patch('flexible_assessment.lti.get_launch_data_storage') as mock_get_launch_data_storage, \
                patch('flexible_assessment.lti.get_launch_url', return_value=self.launch_url):

            # Mock the DjangoOIDCLogin object and its methods
            with patch('flexible_assessment.views.DjangoOIDCLogin') as mock_django_oidc_login:
                oidc_login_instance = MagicMock()
                oidc_login_instance.enable_check_cookies.return_value = oidc_login_instance
                oidc_login_instance.redirect.return_value = HttpResponseRedirect(self.launch_url)
                mock_django_oidc_login.return_value = oidc_login_instance

                response = self.client.get(self.login_url)

                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith(self.launch_url))

                course_data = {
                    'course_id': '12345',
                    'role': 'StudentEnrollment',
                    'user_display_name': 'Test User',
                    'user_id': '987664',
                    'login_id': '987664',
                    'course_name': 'Test Course'
                }

        self.browser = self.launch_new_user(course_data)
        body_text = self.browser.find_element(By.TAG_NAME, 'body').text
        self.assertIn('Test User', body_text)

    @tag('slow', 'view', 'instructor_view')
    @mock_classes.use_mock_canvas()
    def test_view_page(self, mocked_flex_canvas_instance):
        """ Note, this is designed to work with the fixture data for course 1. """
        session_id = self.client.session.session_key
        
        mocked_flex_canvas_instance.groups_dict['2'].grade_list = {'grades': [('1', 50), ('2', 10), ('3', 50), ('4', 60)]}
        
        self.browser.get(self.live_server_url + reverse('instructor:instructor_home', args=[1])) 
        self.browser.add_cookie({'name': 'sessionid', 'value': session_id})

        self.browser.get(self.live_server_url + reverse('instructor:instructor_home', args=[1])) 
        
        input("Press Enter in this terminal to continue")
        
    @tag('slow')
    @mock_classes.use_mock_canvas()
    def test_setup_course(self, mocked_flex_canvas_instance):
        """ In course 2 the teacher is setting up flexible assessment for the first time
            1. Navigate to Course Setup and create 3 assessments
            2. Update MockFlexCanvas grade_list to just have grades for student 1
            3. Match up Assignment Groups
            4. Click on test_student1 and edit their flexes
        """
        print("---------------------test_setup_course-------------------------------")
        
        session_id = self.client.session.session_key
        self.browser.get(self.live_server_url + reverse('instructor:instructor_home', args=[2])) 
        self.browser.add_cookie({'name': 'sessionid', 'value': session_id})
        
        self.browser.get(self.live_server_url + reverse('instructor:instructor_home', args=[2])) 
        
        # 1
        self.browser.find_element(By.LINK_TEXT, "Course Setup").click()
        self.browser.find_element(By.XPATH, '//button[contains(text(), "Assessment")]').click()
        self.browser.find_element(By.XPATH, '//button[contains(text(), "Assessment")]').click()
        self.browser.find_element(By.XPATH, '//button[contains(text(), "Assessment")]').click()
        
        inputs = self.browser.find_elements(By.TAG_NAME, 'input')
        values = ["A1", "33", "30", "50", "A2", "33", "10", "50", "A3", "34", "0", "100"]
        for index, value in enumerate(values):
            inputs[index + 6].send_keys(value) # There are 6 hidden inputs we need to skip over

        date_field = self.browser.find_element(By.NAME, 'date-close')
        
        tomorrow = datetime.now() + timedelta(1)
        date_field.send_keys(datetime.strftime(tomorrow, '%m-%d-%Y'))
        date_field.send_keys(Keys.TAB)
        date_field.send_keys("0245PM")
        
        self.browser.fullscreen_window()
        update_button = self.browser.find_element(By.XPATH, '//button[contains(text(), "Save")]')
        update_button.send_keys(Keys.ENTER)

        wait = WebDriverWait(self.browser, 5)
        wait.until_not(EC.url_contains('form')) # Wait for changes to be made
        
        # 2
        mocked_flex_canvas_instance.canvas_course.groups.pop(0)
        mocked_flex_canvas_instance.groups_dict['2'].grade_list = {'grades': [('1', 40)]}
        mocked_flex_canvas_instance.groups_dict['3'].grade_list = {'grades': [('1', 60)]}
        mocked_flex_canvas_instance.groups_dict['4'].grade_list = {'grades': [('1', 80)]}

        # 3
        self.browser.find_element(By.LINK_TEXT, "Final Grades").click()
        select_tags = self.browser.find_elements(By.TAG_NAME, "select")
        Select(select_tags[0]).select_by_visible_text('test_group2')
        Select(select_tags[1]).select_by_visible_text('test_group4')
        Select(select_tags[2]).select_by_visible_text('test_group3')
        
        self.browser.find_element(By.XPATH, '//button[contains(text(), "Continue")]').click()
        
        # 4 
        bodyText = self.browser.find_element(By.TAG_NAME, 'body').text
        self.assertNotIn('+', bodyText) # With only the default flexes, there is no difference in the totals
        
        self.browser.find_element(By.LINK_TEXT, "test_student1").click()
        inputs = self.browser.find_elements(By.TAG_NAME, 'input')
        inputs[1].send_keys("30")
        inputs[2].send_keys("50")
        inputs[3].send_keys("20")
        inputs[2].click() # This is so the input is registered
        self.browser.find_element(By.XPATH, '//button[contains(text(), "Submit")]').click()
        
        bodyText = self.browser.find_element(By.TAG_NAME, 'body').text
        self.assertIn('+', bodyText)  # Check there is a difference in the totals now
    
    @tag('slow')
    @mock_classes.use_mock_canvas()
    def test_final_grades_matched_then_canvas_group_deleted(self, mocked_flex_canvas_instance):
        """ In course 1 the teacher has matched the flexible assessments to the canvas assignment groups, but then deletes one of the canvas assignment groups
            1. Go to Final Match page and click continue
            2. Delete a canvas assignment group
            3. Go back to the Final Match page. That assignment should no longer be matched
            4. Add back a canvas assignment group and match it then continue
        """
        print("---------------------test_final_grades_matched_then_canvas_group_deleted-------------------------------")
        session_id = self.client.session.session_key
        self.browser.get(self.live_server_url + reverse('instructor:instructor_home', args=[1])) 
        self.browser.add_cookie({'name': 'sessionid', 'value': session_id})
        
        self.browser.get(self.live_server_url + reverse('instructor:instructor_home', args=[1])) 
        # 1
        self.browser.find_element(By.LINK_TEXT, "Final Grades").click()
        self.browser.find_element(By.XPATH, '//button[contains(text(), "Continue")]').click()
        
        # 2
        mocked_flex_canvas_instance.canvas_course.groups.pop(1) # Remove at first element
        
        # 3
        self.browser.find_element(By.LINK_TEXT, "Final Grades").click()
        bodyText = self.browser.find_element(By.TAG_NAME, 'body').text
        self.assertIn('---------', bodyText)
        
        # 4
        mocked_flex_canvas_instance.canvas_course.groups.append(mock_classes.MockAssignmentGroup("NEW GROUP", 2))
        self.browser.refresh()
        self.browser.find_element(By.XPATH, '//*[@id="id_123e4567e89b12d3a456426655440002"]/option[5]').click()
        self.browser.find_element(By.XPATH, '//button[contains(text(), "Continue")]').click()
        
        self.assertIn('final/list', self.browser.current_url)
        
        
    @tag('slow')
    @mock_classes.use_mock_canvas()
    def test_reset_course(self, mocked_flex_canvas_instance):
        """ In course 1 the teacher goes to the assessments view, and deleting all assessments will reset the course
        1. Go to assessments view, make sure there are assessments, student responses, etc.
        2. Delete all the assessments, and submit
        3. Make sure all the data is deleted
        4. Make sure other course data is not deleted
        5. Make sure a student can log in and sets up data correctly
        """
        print("---------------------test_reset_course-------------------------------")
        session_id = self.client.session.session_key
        self.browser.get(self.live_server_url + reverse('instructor:instructor_home', args=[1])) 
        self.browser.add_cookie({'name': 'sessionid', 'value': session_id})
        
        self.browser.get(self.live_server_url + reverse('instructor:instructor_home', args=[1])) 

        # 1
        course = models.Course.objects.get(id=1)
        old_course_id = course.id
        old_course_title = course.title
        userprofiles_before_length = models.UserProfile.objects.all().count()
        course_count_before = models.Course.objects.all().count()
        assessment_count_before = models.Assessment.objects.all().count()
        expected_assessment_count = assessment_count_before - course.assessment_set.all().count()
        comment_count_before = models.UserComment.objects.all().count()
        expected_comment_count = comment_count_before - course.usercomment_set.all().count()
        flexes_count_before = models.FlexAssessment.objects.all().count()
        course_flexes_count = models.FlexAssessment.objects.filter(assessment__course__id=old_course_id).count()
        expected_flex_count_after = flexes_count_before - course_flexes_count

        # 2
        self.browser.find_element(By.LINK_TEXT, "Assessments").click()
        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "delete"))
        )
        buttons = self.browser.find_elements(By.CLASS_NAME, 'delete')

        # Iterate through each button and click it
        for button in buttons:
            if button.is_displayed():
                button.send_keys(Keys.ENTER)
    
        update_button = self.browser.find_element(By.XPATH, '//button[contains(text(), "Update")]')
        update_button.send_keys(Keys.ENTER)
        alert = self.browser.switch_to.alert
        alert.accept()
        wait = WebDriverWait(self.browser, 5)
        wait.until_not(EC.url_contains('form')) # Wait for changes to be made
        
        # 3
        course_after = models.Course.objects.get(id=1)
        user_courses_after = course_after.usercourse_set.all()
        assessments_after = course_after.assessment_set.all()
        comments_after = course_after.usercomment_set.all()
        userprofiles_after = models.UserProfile.objects.all()
        flex_assessments_after = models.FlexAssessment.objects.all()
        self.assertEqual(course_after.id, old_course_id) # Make sure course correctly reset
        self.assertEqual(course_after.title, old_course_title)
        self.assertEqual(course_after.welcome_instructions, models.Course._meta.get_field('welcome_instructions').default)
        self.assertEqual(course_after.comment_instructions, models.Course._meta.get_field('comment_instructions').default)
        self.assertEqual(course_after.open, None)
        self.assertEqual(course_after.close, None)
        self.assertEqual(course_after.id, 1)
        self.assertEqual(user_courses_after.count(), 1) # only one user left (the instructor who made the deletion)

        # 4
        self.assertEqual(assessments_after.count(), 0)
        self.assertEqual(comments_after.count(), 0)
        self.assertEqual(userprofiles_after.count(), userprofiles_before_length) # no user profiles should be deleted
        self.assertEqual(flex_assessments_after.filter(assessment__course__id=course_after.id).count(), 0)
        self.assertEqual(models.FlexAssessment.objects.all().count(), expected_flex_count_after) # Other flexes should not be deleted
        self.assertEqual(models.Course.objects.all().count(), course_count_before)
        self.assertEqual(models.Assessment.objects.all().count(), expected_assessment_count)
        self.assertEqual(models.UserComment.objects.all().count(), expected_comment_count)

        # 5
        student_data = {
            'course_id': course_after.id,
            'role': 'StudentEnrollment',
            'user_display_name': 'Test User',
            'user_id': '987664',
            'login_id': '987664',
            'course_name': course_after.title
        }

        student_browser = self.launch_new_user(student_data) 
        wait = WebDriverWait(student_browser, 5)
        wait.until_not(EC.url_contains('launch')) # Wait for changes to be made
        body_text = student_browser.find_element(By.TAG_NAME, 'body').text
        self.assertIn(course_after.title, body_text)

        # Try logging in old student
        student1_data = {
            'course_id': course_after.id,
            'role': 'StudentEnrollment',
            'user_display_name': 'test_student1',
            'user_id': '1',
            'login_id': '1',
            'course_name': course_after.title
        }
        student_browser = self.launch_new_user(student1_data)
        wait = WebDriverWait(student_browser, 5)
        wait.until_not(EC.url_contains('launch')) # Wait for changes to be made
        body_text = student_browser.find_element(By.TAG_NAME, 'body').text
        self.assertIn(course_after.title, body_text)
        student_browser.close()
