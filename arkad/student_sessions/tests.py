import datetime

from django.test import TestCase, Client
from django.utils import timezone

from companies.models import Company
from student_sessions.models import (
    StudentSession,
    CompanyStudentSessionMotivation,
    StudentSessionApplication,
)
from student_sessions.schema import (
    CreateStudentSessionSchema,
    StudentSessionSchema,
    StudentSessionNormalUserListSchema,
    StudentSessionApplicationSchema,
)
from user_models.models import User
from user_models.schema import ProfileSchema


class StudentSessionTests(TestCase):
    def setUp(self):
        self.company_user1 = User.objects.create_user(
            first_name="Company",
            last_name="Company",
            email="a@company.com",
            password="PASSWORD",
            username="Company",
            is_company=True,
            company=Company.objects.create(name="Orkla"),
        )
        self.company_user2 = User.objects.create_user(
            first_name="Company2",
            last_name="Company2",
            email="a@company.com",
            password="PASSWORD",
            username="Company2",
            is_company=True,
            company=Company.objects.create(name="Axis"),
        )

        self.student_users = []

        for i in range(5):
            self.student_users.append(
                User.objects.create_user(
                    first_name="Student" + str(i),
                    last_name="Student" + str(i),
                    email="a@student.com",
                    password="PASSWORD",
                    username="Student" + str(i),
                    is_student=True,
                    is_company=False,
                )
            )
        self.client = Client()

    @staticmethod
    def _get_auth_headers(user: User) -> dict:
        return {"Authorization": user.create_jwt_token()}

    @staticmethod
    def _session_schema_example(company, **kwargs):
        defaults = dict(
            company_id=company.company_id,
            start_time=timezone.now() + datetime.timedelta(hours=1),
            duration=30,
            booking_close_time=timezone.now() + datetime.timedelta(minutes=10),
        )
        defaults.update(kwargs)
        return CreateStudentSessionSchema(**defaults)

    @classmethod
    def _create_session(cls, company, **kwargs):
        session = StudentSession.objects.create(
            **cls._session_schema_example(company=company, **kwargs).model_dump()
        )
        session.save()
        return session

    def test_get_sessions_noauth(self):
        resp = self.client.get(
            "/api/student-session/all?only_available_sessions=true",
        )
        self.assertEqual(resp.status_code, 200)
        resp2 = self.client.get(
            "/api/student-session/all",
        )
        self.assertEqual(resp2.status_code, 200)

    def test_get_available_sessions(self):
        s1 = self._create_session(self.company_user1)
        s2 = self._create_session(self.company_user2)
        _ = self._create_session(
            self.company_user2, start_time=timezone.now() - datetime.timedelta(hours=1)
        )
        _ = self._create_session(
            self.company_user2,
            booking_close_time=timezone.now() - datetime.timedelta(hours=1),
        )
        resp = self.client.get(
            "/api/student-session/all?only_available_sessions=true",
            headers=self._get_auth_headers(self.student_users[0]),
        )
        self.assertEqual(resp.status_code, 200)
        resp2 = self.client.get(
            "/api/student-session/all",
            headers=self._get_auth_headers(self.student_users[0]),
        )
        self.assertEqual(resp2.status_code, 200)
        data = StudentSessionNormalUserListSchema(**resp.json())
        self.assertEqual(data.numElements, 2)

        sessions = [s.id for s in data.student_sessions]
        self.assertEqual(len(sessions), data.numElements)
        self.assertIn(s1.id, sessions)
        self.assertIn(s2.id, sessions)

    def test_create_student_session(self):
        resp = self.client.post(
            "/api/student-session/exhibitor",
            data=self._session_schema_example(self.company_user1).model_dump(),
            content_type="application/json",
            headers=self._get_auth_headers(self.company_user1),
        )
        self.assertEqual(resp.status_code, 201)

    def test_permission_create_student_session(self):
        resp = self.client.post(
            "/api/student-session/exhibitor",
            data=self._session_schema_example(self.company_user2).model_dump(),
            content_type="application/json",
            headers=self._get_auth_headers(self.company_user1),
        )
        self.assertEqual(resp.status_code, 401)
        resp = self.client.post(
            "/api/student-session/exhibitor",
            data=self._session_schema_example(self.company_user2).model_dump(),
            content_type="application/json",
            headers=self._get_auth_headers(self.student_users[0]),
        )
        self.assertEqual(resp.status_code, 401)

    def test_get_exhibitor_sessions(self):
        sessions = []
        for _ in range(5):
            sessions.append(self._create_session(self.company_user1))
        self.assertEqual(
            401,
            self.client.get(
                "/api/student-session/exhibitor/sessions",
                headers=self._get_auth_headers(self.student_users[0]),
            ).status_code,
        )

        other_company = self.client.get(
            "/api/student-session/exhibitor/sessions",
            headers=self._get_auth_headers(self.company_user2),
        )
        self.assertEqual(200, other_company.status_code)
        data = [StudentSessionSchema(**s) for s in other_company.json()]
        self.assertEqual(len(data), 0)

        correct_company = self.client.get(
            "/api/student-session/exhibitor/sessions",
            headers=self._get_auth_headers(self.company_user1),
        )
        self.assertEqual(200, other_company.status_code)
        data = [StudentSessionSchema(**s) for s in correct_company.json()]
        self.assertEqual(len(data), len(sessions))

    def test_get_applicants(self):
        session = self._create_session(self.company_user1)
        for s in self.student_users:
            motivation = CompanyStudentSessionMotivation.objects.create(
                motivation_text="asd", company=session.company, user=s
            )
            application = StudentSessionApplication.objects.create(
                motivation=motivation
            )
            session.applications.add(application)
        session.save()

        self.assertEqual(
            401,
            self.client.get(
                "/api/student-session/exhibitor/applicants?session_id="
                + str(session.id),
                headers=self._get_auth_headers(self.student_users[0]),
            ).status_code,
        )
        self.assertEqual(
            401,
            self.client.get(
                "/api/student-session/exhibitor/applicants?session_id="
                + str(session.id),
                headers=self._get_auth_headers(self.company_user2),
            ).status_code,
        )
        self.assertEqual(
            404,
            self.client.get(
                "/api/student-session/exhibitor/applicants?session_id="
                + str(session.id + 3),
                headers=self._get_auth_headers(self.company_user1),
            ).status_code,
        )
        resp = self.client.get(
            "/api/student-session/exhibitor/applicants?session_id=" + str(session.id),
            headers=self._get_auth_headers(self.company_user1),
        )
        self.assertEqual(200, resp.status_code)
        data = [ProfileSchema(**p) for p in resp.json()]
        self.assertEqual(len(data), len(self.student_users))

    def test_accept_student_session(self):
        session = self._create_session(self.company_user1)
        session2 = self._create_session(self.company_user1)
        for s in self.student_users:
            motivation = CompanyStudentSessionMotivation.objects.create(
                motivation_text="asd", company=session.company, user=s
            )
            application = StudentSessionApplication.objects.create(
                motivation=motivation
            )
            session.applications.add(application)
            application = StudentSessionApplication.objects.create(
                motivation=motivation
            )
            session2.applications.add(application)
        session.save()
        session2.save()

        url: str = (
            f"/api/student-session/exhibitor/accept?"
            f"session_id={session.id}&applicant_user_id={self.student_users[-1].id}"
        )
        resp = self.client.post(
            url, headers=self._get_auth_headers(self.student_users[0])
        )
        self.assertEqual(401, resp.status_code)

        resp = self.client.post(url, headers=self._get_auth_headers(self.company_user2))
        self.assertEqual(401, resp.status_code)

        resp = self.client.post(url, headers=self._get_auth_headers(self.company_user1))
        self.assertEqual(200, resp.status_code)
        session2.refresh_from_db()
        self.assertFalse(
            session2.applications.filter(id=self.student_users[-1].id).exists()
        )

        url = (
            f"/api/student-session/exhibitor/accept"
            f"?session_id={session.id}&applicant_user_id={self.student_users[-2].id}"
        )
        resp = self.client.post(url, headers=self._get_auth_headers(self.company_user1))
        self.assertEqual(404, resp.status_code)

    def test_apply_for_sessions(self):
        session1 = self._create_session(self.company_user1)
        session2 = self._create_session(self.company_user1)
        url = "/api/student-session/apply"

        resp = self.client.post(
            url,
            data=StudentSessionApplicationSchema(
                motivation_text="love this company", session_id=session1.id
            ).model_dump(),
            content_type="application/json",
            headers=self._get_auth_headers(self.student_users[0]),
        )
        self.assertEqual(200, resp.status_code)

        resp = self.client.post(
            url,
            data=StudentSessionApplicationSchema(
                motivation_text="love this company too", session_id=session2.id
            ).model_dump(),
            content_type="application/json",
            headers=self._get_auth_headers(self.student_users[0]),
        )
        self.assertEqual(200, resp.status_code)

    def test_session_user_validation(self):
        session1 = self._create_session(self.company_user1)
        url = "/api/student-session/apply"

        u = User.objects.create_user(
            email="a@student.com",
            password="PASSWORD",
            username="Student12312",
            is_student=True,
            is_company=False,
        )
        resp = self.client.post(
            url,
            data=StudentSessionApplicationSchema(
                motivation_text="love this company", session_id=session1.id
            ).model_dump(),
            content_type="application/json",
            headers=self._get_auth_headers(u),
        )
        self.assertEqual(409, resp.status_code)

    def test_apply_for_sessions_already_accepted(self):
        session1 = self._create_session(self.company_user1)
        session2 = self._create_session(self.company_user1)
        url = "/api/student-session/apply?session_id="

        resp = self.client.post(
            url,
            data=StudentSessionApplicationSchema(
                motivation_text="good company", session_id=session1.id
            ).model_dump(),
            content_type="application/json",
            headers=self._get_auth_headers(self.student_users[0]),
        )
        self.assertEqual(200, resp.status_code)

        session2.interviewee = self.student_users[1]
        session2.save()

        resp = self.client.post(
            url,
            data=StudentSessionApplicationSchema(session_id=session2.id).model_dump(),
            content_type="application/json",
            headers=self._get_auth_headers(self.student_users[0]),
        )
        self.assertEqual(404, resp.status_code)

    def test_apply_for_multiple_company_sessions(self):
        session1 = self._create_session(self.company_user1)
        session2 = self._create_session(self.company_user1)
        url = "/api/student-session/apply"

        resp = self.client.post(
            url,
            data=StudentSessionApplicationSchema(session_id=session1.id).model_dump(),
            content_type="application/json",
            headers=self._get_auth_headers(self.student_users[0]),
        )
        self.assertEqual(200, resp.status_code)

        session1.interviewee = self.student_users[0]
        session1.save()

        resp = self.client.post(
            url,
            data=StudentSessionApplicationSchema(session_id=session2.id).model_dump(),
            content_type="application/json",
            headers=self._get_auth_headers(self.student_users[0]),
        )
        self.assertEqual(409, resp.status_code)


class StudentSessionMotivationTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="Test Company")

        self.user = User.objects.create_user(
            first_name="student",
            last_name="student",
            email="a@lu.com",
            password="PASSWORD",
            username="Company",
            is_company=False,
        )
        self.client = Client()

    def test_create_motivation(self):
        motivation = CompanyStudentSessionMotivation.objects.create(
            user=self.user, company=self.company, motivation_text="I love this company"
        )
        self.assertEqual(motivation.user, self.user)
        self.assertEqual(motivation.company, self.company)
        self.assertEqual(motivation.motivation_text, "I love this company")

    def test_update_with_api(self):
        motivation = self.client.put(
            "/api/student-session/motivation",
            data={
                "company_id": self.company.id,
                "motivation_text": "I love this company",
            },
            content_type="application/json",
            headers=self.user.get_auth_headers(),
        )
        self.assertEqual(motivation.status_code, 200)
        self.assertEqual(motivation.json(), "I love this company")

    def test_get_student_session_motivation(self):
        _ = CompanyStudentSessionMotivation.objects.create(
            user=self.user, company=self.company, motivation_text="I love this company"
        )
        resp = self.client.get(
            "/api/student-session/motivation?company_id=" + str(self.company.id),
            headers=self.user.get_auth_headers(),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), "I love this company")

    def test_delete_motivation_by_api(self):
        motivation = CompanyStudentSessionMotivation.objects.create(
            user=self.user, company=self.company, motivation_text="I love this company"
        )
        resp = self.client.delete(
            "/api/student-session/motivation?company_id=" + str(self.company.id),
            content_type="application/json",
            headers=self.user.get_auth_headers(),
        )
        self.assertEqual(resp.status_code, 200, resp.json())
        self.assertFalse(
            CompanyStudentSessionMotivation.objects.filter(id=motivation.id).exists()
        )

    def test_get_non_existing_motivation(self):
        resp = self.client.get(
            "/api/student-session/motivation?company_id=" + str(self.company.id),
            headers=self.user.get_auth_headers(),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), None)
