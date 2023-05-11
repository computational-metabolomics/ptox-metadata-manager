from unittest import TestCase
from unittest.mock import patch

from pydrive2.auth import GoogleAuth
from json import dumps

from ptmd.api import app
from ptmd.const import ALLOWED_DOSE_VALUES


class MockGoogleAuth(GoogleAuth):
    credentials = None
    access_token_expired = True

    def LoadCredentialsFile(*args, **kwargs):
        pass

    def LocalWebserverAuth(*args, **kwargs):
        pass

    def SaveCredentialsFile(*args, **kwargs):
        pass

    def Refresh(*args, **kwargs):
        pass

    def Authorize(*args, **kwargs):
        pass

    def SaveCredentials(self, backend=None):
        pass


HEADERS = {'Content-Type': 'application/json'}


def mock_jwt_required(*args, **kwargs):
    return True


# test
@patch('ptmd.api.queries.files.create.session')
@patch('flask_jwt_extended.view_decorators.verify_jwt_in_request', side_effect=mock_jwt_required)
@patch('ptmd.GoogleDriveConnector.upload_file', return_value=({"id": "45", "title": "test", "alternateLink": "a"}))
@patch('ptmd.lib.gdrive.core.GoogleAuth', return_value=MockGoogleAuth)
@patch('ptmd.lib.creator.core.get_chemical_code_mapping', return_value={"chemical1": '001'})
@patch('ptmd.lib.creator.core.get_allowed_organisms', return_value=['organism1'])
@patch('ptmd.lib.creator.core.get_organism_code', return_value=['A'])
@patch('ptmd.lib.creator.core.get_chemical_code_mapping', return_value={'chemical1': '001'})
@patch('ptmd.api.queries.users.login_user', return_value={'access_token': '123'})
@patch('ptmd.api.queries.files.create.get_jwt', return_value={'sub': 1})
@patch('ptmd.api.queries.files.create.Organisation')
@patch('ptmd.database.models.file.Organisation')
@patch('ptmd.database.models.file.Organism')
@patch('ptmd.api.queries.utils.verify_jwt_in_request')
@patch('ptmd.api.queries.utils.get_current_user')
class TestCreateFile(TestCase):
    def test_create_gdrive_file(self, mock_user, mock_jwt_1, mock_organism, mock_organisation_1, mock_organisation_2,
                                mock_sub, mock_login,
                                mock_get_chemicals_mapping, mock_get_organism_code,
                                mock_get_organism, mock_get_chem, mock_upload, mock_auth,
                                mock_jwt, mock_session):
        mock_organisation_2.query.filter().first().gdrive_id = '123'
        mock_organisation_1.query.filter_by().first().organisation_id = 1
        mock_organism.query.filter_by().first().organism_id = 1
        mock_user().role = 'admin'
        with app.test_client() as client:
            data = {
                "partner": "UOB",
                "organism": "organism1",
                "exposure_conditions": [{"chemicals": ["chemical1"], "dose": "BDM10"}],
                "exposure_batch": "AA",
                "replicate4control": 4,
                "replicate4exposure": 4,
                "replicate_blank": 2,
                "start_date": "2021-01-01",
                "end_date": "2022-01-01",
                "timepoints": [3],
                "vehicle": "water",
            }
            response = client.post('/api/files', headers={'Authorization': f'Bearer {123}', **HEADERS},
                                   data=dumps(data))
            self.assertEqual(response.json["message"],
                             f"'exposure' value 'BDM10' is not one of {ALLOWED_DOSE_VALUES}")
            self.assertEqual(response.status_code, 400)

            data["exposure_conditions"][0]["dose"] = "BMD10"
            response = client.post('/api/files', headers={'Authorization': f'Bearer {123}', **HEADERS},
                                   data=dumps(data))
            self.assertEqual(response.json, {'data': {'file_url': 'a'}})
