from .models import Incident


def visible_incidents(user):
    """Return the incidents this user is allowed to see."""
    if user.is_staff:
        return Incident.objects.all()
    return Incident.objects.filter(reporter=user)
