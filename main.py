import pytest
import requests


class RedmineApiWorker:
    def __init__(self, url: str):
        self.url = url

    def get_issue_response(self, issue_id: int) -> requests.Response:
        response = requests.get(self.url + "/issues/" + str(issue_id) + ".json")
        return response

    def add_issue_and_get_response(self, payload: dict, headers: dict) -> requests.Response:
        response = requests.post(self.url + "/issues.json", json=payload, headers=headers)
        return response

    def modify_issue_and_get_response(self, issue_id: int, payload: dict, headers: dict) -> requests.Response:
        response = requests.put(self.url + "/issues/" + str(issue_id) + ".json", json=payload, headers=headers)
        return response


class TestRedmineApi:
    api_worker = RedmineApiWorker('http://62.113.99.40')
    headers = {
        'Content-type': 'application/json',
        'X-Redmine-API-Key': '28146cf406fdbd12615505a7f3f561990687a21a'
    }
    basic_add_issue_params = {
        "issue": {
            "project_id": 1,
            "subject": "Oleg subject",
            "description": "Issue created by Python",
            "priority_id": 4,
            "tracker_id": 3,
            "status_id": 1,
        }}

    basic_modify_issue_params = {
        'issue': {
            'description': 'Update description'
        }
    }

    @pytest.mark.parametrize("add_issue_params, modify_issue_params",
                             [(basic_add_issue_params, basic_modify_issue_params)])
    def test_request_chain_pos(self, add_issue_params: dict, modify_issue_params: dict):
        # Создание задачи
        response = self.api_worker.add_issue_and_get_response(add_issue_params, self.headers)

        assert response.status_code == 201

        issue_id = response.json()['issue']['id']

        # Получение задачи
        response = self.api_worker.get_issue_response(issue_id)

        assert response.status_code == 200
        issue_json = response.json()['issue']
        assert issue_json['project']['id'] == add_issue_params['issue']['project_id']
        assert issue_json['subject'] == add_issue_params['issue']['subject']
        assert issue_json['description'] == add_issue_params['issue']['description']
        assert issue_json['priority']['id'] == add_issue_params['issue']['priority_id']
        assert issue_json['tracker']['id'] == add_issue_params['issue']['tracker_id']
        assert issue_json['status']['id'] == add_issue_params['issue']['status_id']

        # Модификация задачи
        response = self.api_worker.modify_issue_and_get_response(issue_id, modify_issue_params, self.headers)

        assert response.status_code == 204

        # Проверка модификации
        response = self.api_worker.get_issue_response(issue_id)

        assert response.json()['issue']['description'] == modify_issue_params['issue']['description']

    @pytest.mark.parametrize("add_issue_params, modify_issue_params",  # Неверный API-KEY
                             [(basic_add_issue_params, basic_modify_issue_params)])
    def test_request_chain_with_wrong_auth(self, add_issue_params: dict, modify_issue_params: dict):
        wrong_headers = {
            'Content-type': 'application/json',
            'X-Redmine-API-Key': '28146cf406fdbd12615505a7f3f561990687a21g'
        }
        # Создание задачи
        response = self.api_worker.add_issue_and_get_response(add_issue_params, wrong_headers)

        assert response.status_code == 401

        # Модификация задачи
        issue_id = 452

        response = self.api_worker.modify_issue_and_get_response(issue_id, modify_issue_params, wrong_headers)

        assert response.status_code == 401

    @pytest.mark.parametrize("add_issue_params, modify_issue_params",
                             [(basic_add_issue_params, basic_modify_issue_params)])
    def test_request_chain_with_wrong_resource(self, add_issue_params: dict, modify_issue_params: dict):
        # issue не существует

        # Создание задачи
        response = requests.post(self.api_worker.url + "/issue.json", json=add_issue_params, headers=self.headers)

        assert response.status_code == 404
        issue_id = 452
        # Модификация задачи
        response = requests.put(self.api_worker.url + "/issue/" + str(issue_id) + ".json",
                                json=modify_issue_params, headers=self.headers)

        assert response.status_code == 404

    @pytest.mark.parametrize("add_issue_params, modify_issue_params",
                             [(basic_add_issue_params, basic_modify_issue_params)])
    def test_request_chain_with_wrong_issue_id(self, add_issue_params: dict, modify_issue_params: dict):
        # Создание задачи
        response = requests.post(self.api_worker.url + "/issues.json", json=add_issue_params, headers=self.headers)

        # Cозданная задача имеет другой id
        issue_id = 8976

        # Модификация задачи
        response = requests.put(self.api_worker.url + "/issues/" + str(issue_id) + ".json",
                                json=modify_issue_params, headers=self.headers)

        assert response.status_code == 404

    def test_request_chain_with_wrong_json_payload(self):
        # Оба json имеют ошибки
        add_issue_params = '{"issue: {"project_id": 1, "subject": "Oleg subject", ' \
                           '"description": "Issue created by Python", ' \
                           '"priority_id": 4, "tracker_id": 3, "status_id": 1}}'

        modify_issue_params = "{'issue: {'description': 'Update description'}}"

        # Создание задачи
        response = requests.post(self.api_worker.url + "/issues.json", data=add_issue_params, headers=self.headers)

        assert response.status_code == 400

        issue_id = 452

        # Модификация задачи
        response = requests.put(self.api_worker.url + "/issues/" + str(issue_id) + ".json",
                                data=modify_issue_params, headers=self.headers)

        assert response.status_code == 400

    def test_request_chain_with_wrong_params(self):
        # Оба параметра имеют ложные значения
        add_issue_params = '{"issue": {"project_id": 3, "subject": "Oleg subject", ' \
                           '"description": "Issue created by Python", ' \
                           '"priority_id": 4, "tracker_id": 3, "status_id": 1}}'

        modify_issue_params = "{'issue': {'description': ''}}"

        # Создание задачи
        response = requests.post(self.api_worker.url + "/issues.json", data=add_issue_params, headers=self.headers)

        assert response.status_code == 422

        issue_id = 452

        # Модификация задачи
        response = requests.put(self.api_worker.url + "/issues/" + str(issue_id) + ".json",
                                data=modify_issue_params, headers=self.headers)

        assert response.status_code == 400

