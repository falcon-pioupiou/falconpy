# test_authentications.py
# Tests different service class authentication styles
import os
import sys
import pytest
# Authentication via the test_authorization.py
from tests import test_authorization as Authorization
# Import our sibling src folder into the path
sys.path.append(os.path.abspath('src'))
# Classes to test - manually imported from sibling folder
from falconpy import ZeroTrustAssessment, CloudConnectAWS, OAuth2, APIHarness
from falconpy._util import confirm_base_region
from falconpy._version import _TITLE, _VERSION

auth = Authorization.TestAuthorization()
auth.serviceAuth()
AllowedResponses = [200, 401, 403, 429]


class TestAuthentications:

    def serviceAny_TestCredentialAuthFailure(self):
        bad_falcon = ZeroTrustAssessment(creds={"client_id": "This", "client_secret": "WontWork"})
        result = bad_falcon.getAssessmentV1(ids='12345678')

        if result["status_code"] in AllowedResponses:
            return True
        else:
            return False

    def serviceAny_TestBadCredRevoke(self):
        bad_falcon = OAuth2()
        result = bad_falcon.revoke("Will generate a 403")
        if result["status_code"] in AllowedResponses:
            return True
        else:
            return False

    def serviceAny_TestStaleObjectAuth(self):

        falcon = CloudConnectAWS(auth_object=OAuth2(creds={"client_id": auth.config["falcon_client_id"],
                                                           "client_secret": auth.config["falcon_client_secret"]
                                                           }
                                                    ))
        result = falcon.QueryAWSAccounts()
        if result["status_code"] in AllowedResponses:
            return True
        else:
            return False

    def serviceAny_forceCrossCloudResponseFailure(self):
        falcon = OAuth2(client_id=os.environ["CROSS_DEBUG_KEY"],
                        client_secret="will_not_work",
                        base_url="us1"
                        )
        result = falcon.token()
        if result["status_code"] == 403:
            falcon = APIHarness(client_id=os.environ["CROSS_DEBUG_KEY"],
                                client_secret="will_not_work",
                                base_url="us1"
                                )
            t_creds = {
                "client_id": os.environ["CROSS_DEBUG_KEY"],
                "client_secret": "shouldn't work",
            }
            result = falcon.command("oauth2AccessToken", data=t_creds, base_url="us1")
            if result["status_code"] in [401, 403]:
                return True
            else:
                return False
        else:
            return False

    def serviceAny_checkRegionNameLookups(self):
        falcon = OAuth2(client_id=auth.config["falcon_client_id"],
                        client_secret=auth.config["falcon_client_secret"],
                        base_url="usgov1"
                        )
        result = falcon.token()
        if result["status_code"] == 400:
            return True
        elif result["status_code"] == 429:
            pytest.skip("Rate limit hit")
        else:
            return False

    def serviceAny_reallyBadBaseURL(self):
        result = confirm_base_region("https://this-url-does-not-exist")
        if result == "us1":
            return True
        else:
            return False

    def serviceAny_forceGovCloudAutoSelectFailure(self):
        falcon = OAuth2(client_id=os.environ["CROSS_DEBUG_KEY"],
                        client_secret=os.environ["CROSS_DEBUG_SECRET"],
                        base_url="usgov1"
                        )
        result = falcon.token()
        if result["status_code"] == 201:
            falcon = APIHarness(client_id=os.environ["CROSS_DEBUG_KEY"],
                                client_secret=os.environ["CROSS_DEBUG_SECRET"],
                                base_url="usgov1"
                                )
            t_creds = {
                "client_id": os.environ["CROSS_DEBUG_KEY"],
                "client_secret": os.environ["CROSS_DEBUG_SECRET"],
            }
            result = falcon.command("oauth2AccessToken", data=t_creds, base_url="usgov1")
            if result["status_code"] == 201:
                falcon = CloudConnectAWS(client_id=os.environ["CROSS_DEBUG_KEY"],
                                         client_secret=os.environ["CROSS_DEBUG_SECRET"],
                                         base_url="usgov1"
                                         )
                result = falcon.auth_object.token()
                if result["status_code"] == 429:
                    pytest.skip("Rate limit hit")
                if result["status_code"] == 201:
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False

    def serviceAny_TestObjectAuth(self):
        # Should also test direct auth in the authentication class
        auth_obj = OAuth2(client_id=auth.config["falcon_client_id"],
                          client_secret=auth.config["falcon_client_secret"]
                          )
        auth_obj.token()
        # While we're at it, test user_agent override
        falcon = CloudConnectAWS(auth_object=auth_obj, user_agent=f"{_TITLE}/{str(_VERSION)}")
        result = falcon.QueryAWSAccounts()
        if result["status_code"] in AllowedResponses:
            return True
        else:
            return False

    def serviceAny_TestBadObjectAuth(self):
        # Should also test bad direct auth in the authentication class
        falcon = CloudConnectAWS(auth_object=OAuth2())
        result = falcon.QueryAWSAccounts()
        if result["status_code"] in AllowedResponses:
            return True
        else:
            return False

    def test_BadCredentialAuth(self):
        assert self.serviceAny_TestCredentialAuthFailure() is True

    def test_BadCredRevoke(self):
        assert self.serviceAny_TestBadCredRevoke() is True

    def test_StaleObjectAuth(self):
        assert self.serviceAny_TestStaleObjectAuth() is True

    def test_BadObjectAuth(self):
        assert self.serviceAny_TestBadObjectAuth() is True

    def test_badBaseURL(self):
        assert self.serviceAny_reallyBadBaseURL() is True

    def test_crossCloudFailure(self):
        assert self.serviceAny_forceCrossCloudResponseFailure() is True

    @pytest.mark.skipif(auth.authorization.base_url == "https://api.laggar.gcw.crowdstrike.com",
                        reason="Unsupported in GovCloud"
                        )
    def test_checkRegionLookups(self):
        assert self.serviceAny_checkRegionNameLookups() is True

    @pytest.mark.skipif(auth.authorization.base_url == "https://api.laggar.gcw.crowdstrike.com",
                        reason="Unsupported in GovCloud"
                        )
    def test_crossGovCloudSelectFailure(self):
        assert self.serviceAny_forceGovCloudAutoSelectFailure() is True

    def test_ObjectAuth(self):
        assert self.serviceAny_TestObjectAuth() is True
