from flask_testing import TestCase
from app import app, db
from models.user_models import UserModel
from models.problem_models import Problem
import numpy as np
import numpy.testing as npt
import json


class TestProblem(TestCase):
    SQLALCHEMY_DATABASE_URI = "sqlite:///test.db"
    TESTING = True

    def create_app(self):
        app.config["SQLALCHEMY_DATABASE_URI"] = self.SQLALCHEMY_DATABASE_URI
        app.config["TESTING"] = self.TESTING
        return app

    def setUp(self):
        db.create_all()
        self.app = app.test_client()

        db.session.add(UserModel(username="test_user", password=UserModel.generate_hash("pass")))
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_get_problem(self):
        response = self.app.get("/problem/create")

        assert response.status_code == 200

    def test_create_analytical_problem(self):
        payload = json.dumps({"username": "test_user", "password": "pass"})
        response = self.app.post("/login", headers={"Content-Type": "application/json"}, data=payload)
        data = json.loads(response.data)

        access_token = data["access_token"]

        payload = json.dumps(
            {
                "problem_type": "Analytical",
                "name": "analytical_test_problem",
            }
        )

        # Missing objective functions
        response = self.app.post(
            "/problem/create",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"},
            data=payload,
        )

        # 406
        assert response.status_code == 406

        # three objective functions given
        obj_fun_1 = "2*x-y"
        obj_fun_2 = "x+2*y/z"
        obj_fun_3 = "x+y+z"
        objectives = [obj_fun_1, obj_fun_2, obj_fun_3]

        variables = ["x", "y", "z"]

        payload = json.dumps(
            {
                "problem_type": "Analytical",
                "name": "analytical_test_problem",
                "objective_functions": objectives,
                "variables": variables,
            }
        )

        response = self.app.post(
            "/problem/create",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"},
            data=payload,
        )

        assert response.status_code == 201

        # fetch problem and check it
        user_id = UserModel.query.filter_by(username="test_user").first().id

        problem = Problem.query.filter_by(user_id=user_id).first()

        assert problem.name == "analytical_test_problem"
        assert problem.user_id == user_id
        assert problem.problem_type == "Analytical"

        unpickled = problem.problem_pickle

        res = unpickled.evaluate(np.array([[2, 1, 3], [3, 2, 1]])).objectives

        npt.assert_almost_equal(res[0], np.array([3, 2.66666666, 6]))
        npt.assert_almost_equal(res[1], np.array([4, 7, 6]))