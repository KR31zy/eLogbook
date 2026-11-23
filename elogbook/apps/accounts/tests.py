from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model


User = get_user_model()


class PasswordChangeTests(TestCase):
	def setUp(self):
		self.client = Client()
		self.user = User.objects.create_user(username='testuser', email='t@example.com', password='oldpassword')

	def test_get_password_change_requires_login(self):
		url = reverse('accounts:password_change')
		response = self.client.get(url)
		# Should redirect to login
		self.assertEqual(response.status_code, 302)

	def test_password_change_success(self):
		self.client.login(username='testuser', password='oldpassword')
		url = reverse('accounts:password_change')
		response = self.client.get(url)
		self.assertEqual(response.status_code, 200)

		response = self.client.post(url, {
			'old_password': 'oldpassword',
			'new_password1': 'Newpass12345',
			'new_password2': 'Newpass12345',
		})

		# After successful change, should redirect to done page
		self.assertEqual(response.status_code, 302)
		self.assertIn(reverse('accounts:password_change_done'), response['Location'])

		# Verify password actually changed
		self.user.refresh_from_db()
		self.assertTrue(self.user.check_password('Newpass12345'))

	def test_password_change_invalid_current(self):
		self.client.login(username='testuser', password='oldpassword')
		url = reverse('accounts:password_change')
		response = self.client.post(url, {
			'old_password': 'wrongpassword',
			'new_password1': 'Whatever123',
			'new_password2': 'Whatever123',
		})
		# Should return the form with errors
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Your old password was entered incorrectly')

