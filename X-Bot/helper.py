import json
import asyncio
import objects
import aiohttp
import requests
import datetime
import itertools
import exceptions

from random import random
from urllib.parse import urlencode, unquote


index, single_quote = -1, "'"
xbl2_token, xbl3_tokens = None, []
aiohttp_session, requests_session = None, requests.Session()


with open('settings.json') as _file:
    settings = json.load(_file)


def xbl3_token() -> any:
    global index

    index += 1

    if index >= len(xbl3_tokens):
        index = 0

    return xbl3_tokens[index]


def format_device(device: str) -> str:
    if device == 'Scarlett':
        formatted_device = 'Xbox Series S|X'

    elif device == 'XboxOne':
        formatted_device = 'Xbox One'

    elif device == 'Xbox360':
        formatted_device = 'Xbox 360'

    elif device == 'WindowsOneCore' or 'PC':
        formatted_device = 'PC'

    return formatted_device


async def xbl3_token_updater(user_token: str) -> None:
    while True:
        token = await grab_token(user_token, created=True)

        if token is None:
            break

        xbl3_tokens.append(token)

        await asyncio.sleep(57300)

        xbl3_tokens.remove(token)



async def set_session():
    global aiohttp_session

    if aiohttp_session is not None:
        await aiohttp_session.close()
    
    aiohttp_session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False))


async def grab_xuids(gamertag: str) -> list:
    combinations, found = generate_combinations(gamertag), []

    await asyncio.gather(*[find_xuids(combination, found) for combination in combinations])

    xuids = []

    for xuid in found:
        if xuid not in xuids:
            xuids.append(xuid)

    return xuids


async def grab_user_token(email: str, password: str) -> str:
    encoding = unquote(urlencode({
		'client_id': '0000000048093EE3',
		'redirect_uri': 'https://login.live.com/oauth20_desktop.srf',
		'response_type': 'token',
		'display': 'touch',
		'scope': 'service::user.auth.xboxlive.com::MBI_SSL',
		'locale': 'en'
	}))
    
    response = requests_session.get('https://login.live.com/oauth20_authorize.srf?' + encoding)
    
    sft_tag, url_post = response.text.split('sFTTag:\'')[1].split('value="')[1].split('"/>')[0], response.text.split('urlPost:\'')[1].split('\'')[0]
    
    payload = {'login': email, 'passwd': password, 'PPFT': sft_tag}
    
    response = requests_session.post(url_post, data=payload)
    
    payload = {
		'RelyingParty': 'http://auth.xboxlive.com',
		'TokenType': 'JWT',
		'Properties': {
		    'AuthMethod': 'RPS',
		    'SiteName': 'user.auth.xboxlive.com',
		    'RpsTicket': response.url.split('access_token=')[1].split('&token_type=')[0]
		}
	}
	
    response = requests_session.post('https://user.auth.xboxlive.com/user/authenticate', json=payload)
    
    data = response.json()
    
    return data['Token']


async def grab_token(user_token: str, created: bool = False) -> None:
    payload = {
        'RelyingParty': 'http://xboxlive.com' if created else 'http://accounts.xboxlive.com',
        'TokenType': 'JWT',
        'Properties': {
            'UserTokens': [user_token],
            'SandboxId': 'RETAIL'
        }
    }

    async with aiohttp_session.post('https://20.69.107.178:443/xsts/authorize', json=payload) as response:
        if response.status == 200:
            data = await response.json()

            token, uhs, xuid = data['Token'], data['DisplayClaims']['xui'][0]['uhs'], data['DisplayClaims']['xui'][0]['xid']

            return objects.Token(token, uhs, user_token, xuid)

        else:
            return None


def remove_token(token) -> None:
    user_tokens = [user_token.strip() for user_token in open('user_tokens.txt').readlines()]

    with open('user_tokens.txt', 'w') as _file:
        _file.write('\n'.join(user_token for user_token in user_tokens if user_token != token.user_token))

    xbl3_tokens.remove(token)


def generate_combinations(gamertag: str) -> list:
    fixed_gamertag = gamertag.replace(' ', '')

    binary = itertools.product(['', ' '], repeat=len(fixed_gamertag) - 1)
    zipped_binary = (itertools.zip_longest(fixed_gamertag, combination, fillvalue='') for combination in binary)

    combinations = []

    for combination in zipped_binary:
        chain = ''.join(itertools.chain.from_iterable(combination))

        if len(chain) <= 15:
            combinations.append(''.join(character if random()>.5 else character.upper() for character in chain))

    return combinations


async def get_title_history(xuid: str):
    token = xbl3_token()

    headers = {'Authorization': f'XBL3.0 x={token.uhs};{token.token}', 'X-XBL-Contract-Version': '2', 'Accept-Language': 'en-CA, en-GB'}

    async with aiohttp_session.get(f'https://20.80.190.164:443/users/xuid({xuid})/titles/titleHistory/decoration/TitleHistory', headers=headers) as response:
        if response.status == 200:
            data = await response.json()

            try:
                try:
                    first_time_played = datetime.strptime(data['titles'][-1]['titleHistory']['lastTimePlayed'], '%Y-%m-%dT%H:%M:%SZ')
                except:
                    first_time_played = datetime.strptime(data['titles'][-1]['titleHistory']['lastTimePlayed'].split('.')[0], '%Y-%m-%dT%H:%M:%S')

                first_title_name, first_device = format_device(data['titles'][-1]['devices'][0]), data['titles'][-1]['name']

                try:
                    last_time_played = datetime.strptime(data['titles'][0]['titleHistory']['lastTimePlayed'], '%Y-%m-%dT%H:%M:%SZ')
                except:
                    last_time_played = datetime.strptime(data['titles'][0]['titleHistory']['lastTimePlayed'].split('.')[0], '%Y-%m-%dT%H:%M:%S')

                last_title_name, second_device = format_device(data['titles'][0]['devices'][0]), data['titles'][0]['name']

                has_played = True

            except:
                has_played = False

        elif response.status == 401:
            remove_token(token)

            return await get_title_history(xuid)

    if has_played:
        return first_title_name, first_time_played, first_device, last_title_name, last_time_played, second_device

    else:
        raise exceptions.NoTitleHistoryError(f'XUID: {xuid} has no title history!')
 

async def gather_information(xuid: str, options: list):
    token = xbl3_token()

    headers = {'Authorization': f'XBL3.0 x={token.uhs};{token.token}', 'X-XBL-Contract-Version': '5', 'Accept-Language': 'en-CA, en-GB'}

    async with aiohttp_session.get(f'https://20.187.45.173:443/users/me/people/xuids({xuid})/decoration/detail,preferredColor,presenceDetail', headers=headers) as response:
        if response.status == 200:
            data = await response.json()

            information = []

            if 'gamertag' in options:
                information.append(data['people'][0]['gamertag'])

            if 'uniqueModernGamertag' in options:
                information.append(data['people'][0]['uniqueModernGamertag'])

            if 'gamerScore' in options:
                information.append(data['people'][0]['gamerScore'])

            if 'tenure' in options:
                information.append(data['people'][0]['detail']['tenure'])

            if 'displayPicRaw' in options:
                information.append(data['people'][0]['displayPicRaw'].replace('&mode=Padding', ''))

            if 'bio' in options:
                information.append(data['people'][0]['detail']['bio'])

            if 'location' in options:
                information.append(data['people'][0]['detail']['location'])

            if 'realName' in options:
                information.append(data['people'][0]['realName'])

            if 'followerCount' in options:
                information.append(data['people'][0]['detail']['followerCount'])

            if 'followingCount' in options:
                information.append(data['people'][0]['detail']['followingCount'])

            if 'linkedAccounts' in options:
                information.append(data['people'][0]['linkedAccounts'])

            if 'primaryColor' in options:
                information.append(data['people'][0]['preferredColor']['primaryColor'])

            if 'presenceText' in options:
                information.append(data['people'][0]['presenceText'])

            if 'Device' in options:
                try:
                    information.append(format_device(data['people'][0]['presenceDetails'][0]['Device']))
                except:
                    information.append(None)

            return information

        elif response.status == 400:
            raise exceptions.InvalidXUIDError(f'XUID: {xuid} is invalid!')

        elif response.status == 401:
            remove_token(token)

            await gather_information(xuid, options)


async def stats_updater():
    while True:
        balance = 5

        print(f'[Stats Updater] XBL3.0 tokens: {len(xbl3_tokens) * 1:,}', end='\r', flush=True)

        await asyncio.sleep(settings['Application']['Stats updater delay'])


async def find_xuids(gamertag: str, found: list) -> None:
    async with aiohttp_session.get(f'https://20.69.172.119:443/users/gt({gamertag})/profile/settings?settings=Gamertag', headers={'Authorization': xbl2_token, 'X-XBL-Contract-Version': '2'}) as response:
        if response.status == 200:
            data = await response.json()

            gamertag_found_with_services, xuid_found_with_services = data['profileUsers'][0]['settings'][0]['value'], int(data['profileUsers'][0]['id'])

            if gamertag.replace(' ', '').lower() == gamertag_found_with_services.replace(' ', '').lower():
                found.append(f'{xuid_found_with_services}|{gamertag_found_with_services}')

        else:
            xuid_found_with_services = None

    token = xbl3_token()

    headers = {'Authorization': f'XBL3.0 x={token.uhs};{token.token}', 'X-XBL-Contract-Version': '5', 'Accept-Language': 'en-CA, en-GB'}
        
    async with aiohttp_session.get(f'https://20.187.45.173:443/users/me/people/search/decoration/detail?q={gamertag.replace(" ", "%2520")}&maxItems=10', headers=headers) as response:
        if response.status == 200:
            data = await response.json()

            for index, _ in enumerate(data['people']):
                gamertag_found_with_peoplehub, xuid_found_with_peoplehub = data['people'][index]['gamertag'], int(data['people'][index]['xuid'])

                if gamertag.replace(' ', '').lower() == gamertag_found_with_peoplehub.replace(' ', '').lower() and xuid_found_with_peoplehub != xuid_found_with_services:
                    found.append(f'{xuid_found_with_peoplehub}|{gamertag_found_with_peoplehub}')

        elif response.status == 401:
            remove_token(token)
            
            await find_xuids(gamertag, found)


async def convert_user_token(user_token: str) -> None:
    token = await grab_token(user_token)

    payload = {
        'dateOfBirth': '2000-01-01T00:00:00.0000000',
        'email': '',
        'firstName': '',
        'gamerTag': '',
        'gamerTagChangeReason': None,
        'homeAddressInfo': {
            'city': None,
            'country': 'US',
            'postalCode': None,
            'state': None,
            'street1': None,
            'street2': None
        },
        'homeConsole': None,
        'imageUrl': '',
        'isAdult': True,
        'lastName': '',
        'legalCountry': 'US',
        'locale': 'en-US',
        'midasConsole': None,
        'msftOptin': True,
        'ownerHash': None,
        'ownerXuid': None,
        'partnerOptin': True,
        'requirePasskeyForPurchase': False,
        'requirePasskeyForSignIn': False,
        'subscriptionEntitlementInfo': None,
        'touAcceptanceDate': '2000-01-01T00:00:00.0000000',
        'userHash': token.uhs,
        'userKey': None,
        'userXuid': '216258806147975844'
    }

    async with aiohttp_session.post('https://accountstroubleshooter.xboxlive.com/users/current/profile', headers={'Authorization': f'XBL3.0 x={token.uhs};{token.token}', 'X-XBL-Contract-Version': '4'}, json=payload) as response:
        return response.status


async def xbl2_token_updater():
    global xbl2_token
    
    while True:
        with requests.Session() as session:
            try:
                encoded_url = urlencode({
		            'client_id': '0000000048093EE3',
		            'redirect_uri': 'https://login.live.com/oauth20_desktop.srf',
		            'response_type': 'token',
		            'display': 'touch',
		            'scope': 'service::live.xbox.com::MBI_SSL',
		            'locale': 'en'
		        })

                response = session.get('https://login.live.com:443/oauth20_authorize.srf?' + encoded_url)

                sft_tag, url_post = response.text.split('sFTTag:\'')[1].split('value="')[1].split('"/>')[0], response.text.split('urlPost:\'')[1].split('\'')[0]

                payload = {'login': settings['Xbox account (Format: Email|Password)'].split('|')[0], 'passwd': settings['Xbox account (Format: Email|Password)'].split('|')[1], 'PPFT': sft_tag}

                response = session.post(url_post, data=payload)

                access_token = response.url.split('access_token=')[1].split('&token_type=')[0]

                headers = {'Authorization': f'WLID1.0 t={access_token}', 'Content-Type': 'application/soap+xml; charset=utf-8'}

                payload = '''
		        <s:Envelope
	                xmlns:s='http://www.w3.org/2003/05/soap-envelope'
	                xmlns:a='http://www.w3.org/2005/08/addressing'>
	                <s:Header>
		    			<a:Action s:mustUnderstand='1'>http://docs.oasis-open.org/ws-sx/ws-trust/200512/RST/Issue</a:Action>
		    			<a:MessageID>urn:uuid:2bd42a2f-8999-45a7-83f2-f0aab2d2a117</a:MessageID>
		    			<a:ReplyTo>
		    				<a:Address>http://www.w3.org/2005/08/addressing/anonymous</a:Address>
		    			</a:ReplyTo>
		    			<a:To s:mustUnderstand='1'>http://activeauth.xboxlive.com//XSts/xsts.svc/IWSTrust13</a:To>
		    		</s:Header>
		    		<s:Body>
		    			<trust:RequestSecurityToken
		    				xmlns:trust='http://docs.oasis-open.org/ws-sx/ws-trust/200512'>
		    				<wsp:AppliesTo
		    					xmlns:wsp='http://schemas.xmlsoap.org/ws/2004/09/policy'>
		    					<EndpointReference
		    						xmlns='http://www.w3.org/2005/08/addressing'>
		    						<Address>http://xboxlive.com</Address>
		    					</EndpointReference>
		    				</wsp:AppliesTo>
		    				<trust:KeyType>http://docs.oasis-open.org/ws-sx/ws-trust/200512/Bearer</trust:KeyType>
		    				<trust:RequestType>http://docs.oasis-open.org/ws-sx/ws-trust/200512/Issue</trust:RequestType>
		    				<trust:TokenType>http://docs.oasis-open.org/wss/oasis-wss-saml-token-profile-1.1#SAMLV2.0</trust:TokenType>
		    			</trust:RequestSecurityToken>
		    		</s:Body>
		    	</s:Envelope>
		        '''

                response = session.post('https://activeauth.xboxlive.com:443/XSts/xsts.svc/IWSTrust13', headers=headers, data=payload)

                security_token = str(response.content).split('</e:EncryptionMethod><KeyInfo><o:SecurityTokenReference')[1].split('</trust:RequestedSecurityToken><trust:R')[0]

                xbl2_token = f'XBL2.0 x=<EncryptedAssertion xmlns="urn:oasis:names:tc:SAML:2.0:assertion"><xenc:EncryptedData Type="http://www.w3.org/2001/04/xmlenc#Element" xmlns:xenc="http://www.w3.org/2001/04/xmlenc#"><xenc:EncryptionMethod Algorithm="http://www.w3.org/2001/04/xmlenc#aes256-cbc"/><KeyInfo xmlns="http://www.w3.org/2000/09/xmldsig#"><e:EncryptedKey xmlns:e="http://www.w3.org/2001/04/xmlenc#"><e:EncryptionMethod Algorithm="http://www.w3.org/2001/04/xmlenc#rsa-oaep-mgf1p"><DigestMethod Algorithm="http://www.w3.org/2000/09/xmldsig#sha1"/></e:EncryptionMethod><KeyInfo><o:SecurityTokenReference{security_token}'

                await asyncio.sleep(14100)

            except:
                pass
