import re
import urllib
import urllib2
import json
import base64
import time


class Client2(object):
    """ 
    OAuth 2 helper. 
    
    A client is constructed with the client credentials, auth server info, grant permissions required
    and optionally existing access token info if one has already been obtained.
    
    One of 4 grant types can be used to obtain an access token. See the following methods:
        auth_code_grant
        implicit_grant
        resource_owner_credentials_grant
        client_credentials_grant
        
    Once an access token has been obtained, the access_resource method can be used to make authenticated requests. The 
    client will automatically request a new access token if required and if possible.
    
    Token info should be read from the following properties and persisted between application runs:
        token_type
        access_token
        access_token_expire_time
        refresh_token
    """

    # expose attributes as read-only properties
    id = property(lambda self: self._id)
    secret = property(lambda self: self._secret)
    auth_endpoint = property(lambda self: self._auth_endpoint)
    token_endpoint = property(lambda self: self._token_endpoint)
    auth_redirect_uri = property(lambda self: self._auth_redirect_uri)
    scope = property(lambda self: self._scope)
    token_type = property(lambda self: self._token_type)
    access_token = property(lambda self: self._access_token)
    access_token_expire_time = property(lambda self: self._access_token_expire_time)
    refresh_token = property(lambda self: self._refresh_token)

    def __init__(self, id, secret, auth_endpoint, token_endpoint, auth_redirect_uri, scope=None, token_type=None, 
                 refresh_token=None, access_token=None, access_token_expire_time=None):
        """Constructs a new OAuth2 client with the following parameters:
            id                       - The client id obtained when the application was registered
            secret                   - The client secret obtained when the application was registered
            auth_endpoint            - URL on the auth server to use for authentication requests
            token_endpoint           - URL on the auth server to use for obtaining access tokens
            auth_redirect_uri        - Application URL to redirect resource owner back to with new grant info
            scope                    - (Optional) Sequence of strings indicating required permissions
            token_type               - (Optional) Type of access token if one has already been obtained
            refresh_token            - (Optional) Refresh token if one has already been obtained
            access_token             - (Optional) Access token if one has already been obtained
            access_token_expire_time - (Optional) Epoch seconds at which access token will expire, if one has already 
                                       been obtained"""
        self._id = id
        self._secret = secret
        self._auth_endpoint = auth_endpoint
        self._token_endpoint = token_endpoint
        self._auth_redirect_uri = auth_redirect_uri
        self._scope = scope
        if access_token is not None:
            if not self._is_valid_token_type(token_type):
                raise ValueError('Unsupported token type "{}"'.format(token_type))
            self._token_type = token_type    
            self._access_token = access_token
            self._access_token_expire_time = access_token_expire_time
        else:
            self._token_type = None
            self._access_token = None
            self._access_token_expire_time = None            
        self._refresh_token = refresh_token
        
    def make_auth_code_grant_url(self, state=None):
        """Returns a url that the resource owner should be directed to in order to grant access permission for an
           authorization code grant. They will be redirected to the auth_redirect_uri."""
        params = {'client_id': self._id, 'redirect_uri': self._auth_redirect_uri, 'response_type': 'code'}
        if state is not None: params['state'] = state
        if self._scope is not None: params['scope'] = ' '.join(self._scope)
        return self._auth_endpoint + '?' + urllib.urlencode(params)

    def auth_code_grant(self, auth_code):
        """Should be called on receipt of an auth code grant callback request. Attempts to obtain an access token
           using the given authorization code"""
        params = {'grant_type': 'authorization_code', 'code': auth_code, 'redirect_uri': self._auth_redirect_uri}
        self._grant_request(params)
            
    def make_implicit_grant_url(self, state=None):
        """Returns a url that the resource owner should be directed to in order to grant access permission for an
           implicit grant"""
        params = {'client_id': self._id, 'response_type': 'token', 'redirect_uri': self._auth_redirect_uri}
        if state is not None: params['state'] = state
        if self._scope is not None: params['scope'] = ' '.join(self._scope)
        return self._auth_endpoint + '?' + urllib.urlencode(params)        
        
    def implicit_grant(self, token_type, access_token, expires_in=None):
        """Should be called on receipt of an implicit grant callback request"""
        if not self._is_valid_token_type(token_type):
            raise OAuthError('Unsupported token type "{}"'.format(token_type))
        self._token_type = token_type
        self._access_token = access_token
        if expires_in:
            self._access_token_expire_time = time.time() + int(expires_in)
        else:
            self._access_token_expire_time = None
        self._refresh_token = None
            
    def resource_owner_credentials_grant(self, username, password):
        """Attempts to obtain an access token using the given resource owner credentials"""
        params = {'grant_type': 'password', 'username': username, 'password': password}
        if self._scope is not None:
            params['scope'] = ' '.join(self._scope)
        self._grant_request(params)

    def client_credentials_grant(self):
        """Attempts to obtain an access token using the client's credentials"""
        params = {'grant_type': 'client_credentials'}
        if self._scope is not None:
            params['scope'] = ' '.join(self._scope)
        self._grant_request(params)
            
    def access_resource(self, request_obj):
        """Makes an authenticated request. request_obj is a urllib2.Request object which will have authentication info
        added to it before sending. Returns the response if available"""
        
        if not self._has_valid_access_token():
            self._attempt_token_refresh()
                   
        # request attempt loop
        for attempt_num in range(2):
        
            # prepare request with credentials    
            if self._token_type == 'bearer':
                request_obj.headers['Authorization'] = 'Bearer '+self._access_token
        
            try:
                return urllib2.urlopen(request_obj)
            except urllib2.HTTPError as e:
                if e.code == 401 and self._extract_authentication_error(e) == 'invalid_token':
                    self._access_token = None
                    self._access_token_expire_time = None
                    self._attempt_token_refresh()
                    continue  # try again with new token
                elif e.code == 403 and self._extract_authentication_error(e) == 'insufficient_scope':
                    raise InsufficientScopeError('Scope of grant is not sufficient to access this resource')
                else:
                    raise e
                    
        raise OAuthError("Invalid access token even after refresh")
            
    def _has_valid_access_token(self):
        if self._access_token is None: 
            return False
        if self._access_token_expire_time is not None and time.time() > self._access_token_expire_time:
            return False
        return True
                
    def _extract_authentication_error(self, response):
        authenticate_parts = response.headers.get('WWW-Authenticate','').split(' ',1)
        if authenticate_parts[0].lower() == self._token_type and len(authenticate_parts) > 1:
            authenticate_params = dict(re.match(r'^ *([^ =]+) *= *"([^"]*)"$', x).groups() 
                                       for x in authenticate_parts[1].split(','))
            return authenticate_params.get('error','')
        return ''
        
    def _attempt_token_refresh(self):
        self._access_token = None
        self._access_token_expire_time = None
        if self._refresh_token is None:
            self._raise_no_refresh_error()
        params = {'grant_type': 'refresh_token', 'refresh_token': self._refresh_token}
        if self._scope is not None:
            params['scope'] = ' '.join(self._scope)
        # dumb hack - save refresh token in case its omitted from response and removed
        refresh_token = self._refresh_token
        self._grant_request(params)
        if self._refresh_token is None:
            self._refresh_token = refresh_token
        if not self._has_valid_access_token():
            self._raise_no_refresh_error()
        
    def _raise_no_refresh_error(self):
        raise GrantRequiredError('No valid access token could be obtained. Request new grant')        
        
    def _is_valid_token_type(self, token_type):
        return token_type == 'bearer'
        
    def _request(self, endpoint, params):
        auth_header = 'Basic '+base64.b64encode(urllib.quote(self._id,'')+':'+urllib.quote(self._secret,''))
        request = urllib2.Request(endpoint, urllib.urlencode(params), 
                                  {'Authorization': auth_header, 'Content-Type': 'application/x-www-form-urlencoded'})
        try:
            response = urllib2.urlopen(request)
        except urllib2.HTTPError as e:
            errordesc = ''
            if e.code==400 and self._is_json_response(e):
                try:
                    jdata = json.load(e)
                    errordesc = '{} {}'.format(jdata.get('error',''), jdata.get('error_description',''))
                except ValueError: 
                    pass            
            raise OAuthError('Error response from request', e, errordesc)
        except IOError as e:
            raise OAuthError('Failed to complete request', e)
        if not self._is_json_response(response):
            raise OAuthError('Expected JSON encoded response')
        try:
            jdata = json.load(response)
        except ValueError as e:
            raise OAuthError('Failed to parse JSON', e)
        return jdata
        
    def _grant_request(self, params):
        jdata = self._request(self._token_endpoint, params)
        print jdata
        token_type = jdata.get('token_type',None)
        if token_type is not None: token_type = token_type.lower()
        if not self._is_valid_token_type(token_type):
            raise OAuthError('Received unsupported token type "{}"'.format(token_type))
        self._token_type = token_type
        self._access_token = jdata.get('access_token', None)
        if self._access_token is None:
            raise OAuthError('No access token was received from the grant request')
        expires_in = jdata.get('expires_in',None)
        if expires_in is not None:
            self._access_token_expire_time = time.time() + int(expires_in)
        else:
            self._access_token_expire_time = None
        self._refresh_token = jdata.get('refresh_token', None)
                    
    def _is_json_response(self, response):
        return response.headers.get('Content-Type','').split(';')[0].endswith('/json')


class OAuthError(Exception):
    pass
    
class GrantRequiredError(OAuthError):
    pass

class InsufficientScopeError(OAuthError):
    pass
