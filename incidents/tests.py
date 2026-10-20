from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase

from .models import Incident


class IncidentModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.reporter = User.objects.create_user(username="reporter", password="test-pass-123")
        cls.assignee = User.objects.create_user(username="assignee", password="test-pass-123")

    def make_incident(self, **overrides):
        data = {"title": "500 error", "description": "Checkout fails", "reporter": self.reporter}
        data.update(overrides)
        return Incident(**data)

    def test_valid_incident_passes_validation(self):
        incident = self.make_incident()
        incident.full_clean()

    def test_missing_title_fails_validation(self):
        incident = self.make_incident(title="")
        with self.assertRaises(ValidationError) as cm:
            incident.full_clean()
        self.assertIn("title", cm.exception.message_dict)
    
    def test_missing_description_fails_validation(self):
        incident = self.make_incident(description="")
        with self.assertRaises(ValidationError) as cm:
            incident.full_clean()
        self.assertIn("description", cm.exception.message_dict)
    
    def test_invalid_severity_fails(self):
        incident = self.make_incident(severity="okay")
        with self.assertRaises(ValidationError) as cm:
            incident.full_clean()
        self.assertIn("severity", cm.exception.message_dict)
    
    def test_related_names_returns_reports(self):
        incident = self.make_incident(assignee=self.assignee)
        incident.save()
        self.assertIn(incident, self.reporter.reports.all())
        self.assertIn(incident, self.assignee.assigned_incidents.all())
    
    def test_deleting_reporter_is_protected(self):
        incident = self.make_incident()
        incident.save()
        with self.assertRaises(ProtectedError):
            incident.reporter.delete()
    
    def test_deleting_assignee_leaves_assignee_field_blank(self):
        incident = self.make_incident()
        incident.assignee = self.assignee
        incident.save()
        self.assignee.delete()
        incident.refresh_from_db()
        self.assertIsNone(incident.assignee)
    
    def test_defaults(self):
        incident = self.make_incident()
        self.assertEqual(incident.severity, Incident.Severity.MEDIUM)
        self.assertEqual(incident.status, Incident.Status.OPEN)


class IncidentAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.creator = User.objects.create_superuser(username="user1", password="test-pass-123")
        cls.editor = User.objects.create_superuser(username="user2", password="test-pass-123")

    def form_data(self, **overrides):
        data = {
            "title": "500 error",
            "description": "Checkout fails",
            "severity": "medium",
            "status": "open",
            "assignee": "",
        }
        data.update(overrides)
        return data

    def test_reporter_set_on_create(self):
        self.client.force_login(self.creator)
        response = self.client.post(reverse("admin:incidents_incident_add"), self.form_data())
        self.assertEqual(response.status_code, 302)
        incident = Incident.objects.get()
        self.assertEqual(incident.reporter, self.creator)

    def test_reporter_unchanged_when_another_user_edits(self):
        incident = Incident.objects.create(
            title="500 error",
            description="Upload fails",
            reporter=self.creator
        )
        self.client.force_login(self.editor)
        url = reverse("admin:incidents_incident_change", args=[incident.pk])
        response = self.client.post(url, self.form_data(title="Updated title"))
        self.assertEqual(response.status_code, 302)

        incident.refresh_from_db()
        self.assertEqual(incident.title, "Updated title")
        self.assertEqual(incident.reporter, self.creator)


class IncidentAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(username="user", password="test-pass-123")
        cls.other_user = User.objects.create_user(username="other_user", password="test-pass-123")
        cls.url = reverse("incident-list")

    def test_list_refused_for_logged_out_users(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
    
    def test_create_sets_reporter_to_logged_in_user(self):
        self.client.force_authenticate(user=self.user)
        data = {"title": "404 error", "description": "page not found"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 201)
        incident = Incident.objects.get()
        self.assertEqual(incident.reporter, self.user)
    
    def test_client_cannot_set_reporter(self):
        self.client.force_authenticate(user=self.user)
        data = {"title": "404 error", "description": "page not found", "reporter": self.other_user.pk}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 201)
        incident = Incident.objects.get()
        self.assertEqual(incident.reporter, self.user)
    
    def test_client_cannot_change_reporter_on_update(self):
        incident = Incident.objects.create(title="404", description="page not found", reporter=self.user)
        self.client.force_authenticate(user=self.user)
        url = reverse("incident-detail", args=[incident.pk])
        response = self.client.patch(url, {"reporter": self.other_user.pk}, format="json")
        self.assertEqual(response.status_code, 200)
        incident.refresh_from_db()
        self.assertEqual(incident.reporter, self.user)

    def test_create_sets_severity_to_medium(self):
        self.client.force_authenticate(user=self.user)
        data = {"title": "404 error", "description": "page not found"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, 201)
        incident = Incident.objects.get()
        self.assertEqual(incident.severity, Incident.Severity.MEDIUM)
        self.assertEqual(response.data["severity"], Incident.Severity.MEDIUM)


class IncidentPermissionTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(username="user", password="test-pass-123")
        cls.other_user = User.objects.create_user(username="other_user", password="test-pass-123")
        cls.staff = User.objects.create_user(username="staff", password="test-pass-123", is_staff=True)
        cls.own_incident = Incident.objects.create(title="Mine", description="x", reporter=cls.user)
        cls.other_incident = Incident.objects.create(title="Theirs", description="y", reporter=cls.other_user)
        cls.list_url = reverse("incident-list")
    
    def test_normal_user_only_sees_their_incidents(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.list_url)
        ids = [item["id"] for item in response.data]
        self.assertEqual(ids, [self.own_incident.pk])
    
    def test_normal_user_gets_404_viewing_other_user_incidents(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("incident-detail", args=[self.other_incident.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
    
    def test_staff_user_sees_all_incidents(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(self.list_url)
        ids = [item["id"] for item in response.data]
        self.assertCountEqual(ids, [self.own_incident.pk, self.other_incident.pk])
    
    def test_cannot_delete_using_api(self):
        self.client.force_authenticate(user=self.staff)
        url = reverse("incident-detail", args=[self.own_incident.pk])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Incident.objects.filter(pk=self.own_incident.pk).exists())
    
    def test_cannot_delete_in_admin(self):
        User = get_user_model()
        super_user = User.objects.create_superuser(username="superuser", password="test-pass-123")
        self.client.force_login(user=super_user)
        url = reverse("admin:incidents_incident_delete", args=[self.own_incident.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)