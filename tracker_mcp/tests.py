from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from django_mcpz.bearer_tokens.models import Token

from incidents.models import Incident


class MCPTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.staff = User.objects.create_user(username="staff", password="test-pass-123", is_staff=True)
        cls.alice = User.objects.create_user(username="alice", password="test-pass-123")
        cls.bob = User.objects.create_user(username="bob", password="test-pass-123")
        cls.alice_incident_one = Incident.objects.create(title="open1", description="first", reporter=cls.alice, status=Incident.Status.OPEN, severity=Incident.Severity.HIGH)
        cls.alice_incident_two = Incident.objects.create(title="open2", description="second", reporter=cls.alice, status=Incident.Status.OPEN, severity=Incident.Severity.LOW)
        cls.alice_incident_three = Incident.objects.create(title="investigating", description="third", reporter=cls.alice, status=Incident.Status.INVESTIGATING, severity=Incident.Severity.HIGH)
        cls.bob_incident = Incident.objects.create(title="open3", description="fourth", reporter=cls.bob, status=Incident.Status.OPEN, severity=Incident.Severity.CRITICAL)
        Incident.objects.filter(pk=cls.alice_incident_two.pk).update(created_at=timezone.now() - timedelta(days=10))
        _, cls.staff_token = Token.create(name="staff test", user=cls.staff)
        _, cls.alice_token = Token.create(name="alice test", user=cls.alice)
        _, cls.bob_token = Token.create(name="bob test", user=cls.bob)
    
    def call_tool(self, token, name, arguments=None):
        body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments or {}},
        }
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        return self.client.post("/mcp/", body, content_type="application/json", headers=headers)
    
    def test_no_token_returns_401(self):
        response = self.call_tool(None, "count_open_incidents")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers["WWW-Authenticate"], "Bearer")
    
    def test_user_cannot_get_another_users_incident(self):
        arguments = {"incident_id": self.bob_incident.pk}
        own = self.call_tool(self.bob_token, "get_incident", arguments)
        self.assertTrue(own.json()["result"]["structuredContent"]["found"])
        other = self.call_tool(self.alice_token, "get_incident", arguments)
        result = other.json()["result"]["structuredContent"]
        self.assertFalse(result["found"])
        self.assertIsNone(result.get("incident"))
