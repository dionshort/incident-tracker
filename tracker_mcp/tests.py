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
        cls.alice_incident_one = Incident.objects.create(title="open1", description="first", reporter=cls.alice, assignee=cls.staff, status=Incident.Status.OPEN, severity=Incident.Severity.HIGH)
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
    
    def test_count_open_incidents_is_scoped_to_user(self):
        staff_response = self.call_tool(self.staff_token, "count_open_incidents")
        result_one = staff_response.json()["result"]["structuredContent"]
        self.assertEqual(result_one["count"], 3)
        alice_response = self.call_tool(self.alice_token, "count_open_incidents")
        result_two = alice_response.json()["result"]["structuredContent"]
        self.assertEqual(result_two["count"], 2)
    
    def test_list_open_incidents_is_scoped_to_user(self):
        response = self.call_tool(self.alice_token, "list_open_incidents")
        incidents = response.json()["result"]["structuredContent"]["incidents"]
        ids = [incident["id"] for incident in incidents]
        severities = [incident["severity"] for incident in incidents]
        self.assertEqual(ids, [self.alice_incident_one.pk, self.alice_incident_two.pk])
        self.assertEqual(severities, ["high", "low"])
        arguments = {"limit": 1}
        limit_response = self.call_tool(self.alice_token, "list_open_incidents", arguments)
        limit_incident = limit_response.json()["result"]["structuredContent"]
        self.assertEqual(len(limit_incident["incidents"]), 1)
        self.assertEqual(limit_incident["incidents"][0]["id"], self.alice_incident_one.pk)
    
    def test_get_own_incident_returns_details(self):
        arguments_bob = {"incident_id": self.bob_incident.pk}
        arguments_alice = {"incident_id": self.alice_incident_one.pk}
        own = self.call_tool(self.bob_token, "get_incident", arguments_bob)
        other = self.call_tool(self.alice_token, "get_incident", arguments_alice)
        result = own.json()["result"]["structuredContent"]
        self.assertTrue(result["found"])
        self.assertTrue(other.json()["result"]["structuredContent"]["found"])
        self.assertEqual(other.json()["result"]["structuredContent"]["incident"]["assignee"], "staff")
        incident = result["incident"]
        self.assertEqual(incident["description"], "fourth")
        self.assertEqual(incident["reporter"], "bob")
        self.assertIsNone(incident["assignee"])
        self.assertEqual(incident["id"], self.bob_incident.pk)
        self.assertEqual(incident["severity"], "critical")
        self.assertEqual(incident["title"], "open3")
        self.assertEqual(incident["status"], "open")
    
    def test_count_by_status_includes_statuses(self):
        alice_incidents = self.call_tool(self.alice_token, "count_incidents_by_status")
        result = alice_incidents.json()["result"]["structuredContent"]
        self.assertEqual(result["counts"], [
            {"status": "open", "count": 2},
            {"status": "investigating", "count": 1},
            {"status": "resolved", "count": 0},
        ])
    
    def test_list_open_incidents_rejects_limit_0(self):
        arguments = {"limit": 0}
        response = self.call_tool(self.alice_token, "list_open_incidents", arguments)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["result"]["isError"])
    
    def test_hidden_incident_looks_the_same_as_missing_one(self):
        missing_id = Incident.objects.latest("pk").pk + 1
        self.assertFalse(Incident.objects.filter(pk=missing_id).exists())
        hidden = self.call_tool(self.alice_token, "get_incident", {"incident_id": self.bob_incident.pk})
        missing = self.call_tool(self.alice_token, "get_incident", {"incident_id": missing_id})
        self.assertEqual(hidden.json()["result"]["structuredContent"], missing.json()["result"]["structuredContent"])
