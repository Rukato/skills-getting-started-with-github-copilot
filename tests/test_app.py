import copy
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    # Arrange: capture current activity state
    original = copy.deepcopy(activities)
    yield
    # Cleanup: restore activity participants after each test
    for name, activity in original.items():
        activities[name]["participants"] = list(activity["participants"])


def test_root_redirect(client):
    # Arrange
    url = "/"

    # Act
    response = client.get(url, follow_redirects=False)

    # Assert
    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_all(client):
    # Arrange
    url = "/activities"

    # Act
    response = client.get(url)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert "Programming Class" in data


@pytest.mark.parametrize(
    "activity_name,email",
    [
        ("Gym Class", "test1@mergington.edu"),
        ("Tennis Club", "test2@mergington.edu"),
    ],
)
def test_signup_for_activity_success(client, activity_name, email):
    # Arrange
    url = f"/activities/{activity_name}/signup"
    params = {"email": email}
    assert email not in activities[activity_name]["participants"]

    # Act
    response = client.post(url, params=params)

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities[activity_name]["participants"]


def test_signup_for_activity_not_found(client):
    # Arrange
    url = "/activities/Nonexistent Activity/signup"
    params = {"email": "missing@mergington.edu"}

    # Act
    response = client.post(url, params=params)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_for_activity_already_registered(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    url = f"/activities/{activity_name}/signup"
    params = {"email": email}
    assert email in activities[activity_name]["participants"]

    # Act
    response = client.post(url, params=params)

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


@pytest.mark.parametrize(
    "activity_name,email",
    [
        ("Basketball Team", "alumni@mergington.edu"),
        ("Art Studio", "artlover@mergington.edu"),
    ],
)
def test_remove_signup_success(client, activity_name, email):
    # Arrange
    activities[activity_name]["participants"].append(email)
    url = f"/activities/{activity_name}/signup"
    params = {"email": email}
    assert email in activities[activity_name]["participants"]

    # Act
    response = client.delete(url, params=params)

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}
    assert email not in activities[activity_name]["participants"]


def test_remove_signup_activity_not_found(client):
    # Arrange
    url = "/activities/Unknown Activity/signup"
    params = {"email": "noone@mergington.edu"}

    # Act
    response = client.delete(url, params=params)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_signup_student_not_signed(client):
    # Arrange
    activity_name = "Science Club"
    url = f"/activities/{activity_name}/signup"
    params = {"email": "unlisted@mergington.edu"}
    assert "unlisted@mergington.edu" not in activities[activity_name]["participants"]

    # Act
    response = client.delete(url, params=params)

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student not signed up for this activity"
