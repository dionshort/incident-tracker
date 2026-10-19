from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.test import TestCase

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