from crewai_tools.tools.base_tool import BaseTool
import os, base64, json, logging, warnings
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email.mime.text import MIMEText

warnings.filterwarnings("ignore", category=Warning, module="googleapiclient.discovery")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GmailTool(BaseTool):
    name: str = "GmailTool"
    description: str = "Tool to read unread emails and create draft replies using Gmail API. Actions: 'read_unread_emails', 'create_draft'."

    def _run(self, action: str, params: dict = None) -> str:
        logger.info(f"Executing action: {action} with params: {params}")
        creds = self._get_credentials()
        service = build('gmail', 'v1', credentials=creds, cache_discovery=False)

        if action == "read_unread_emails":
            return self._read_unread_emails(service, params or {})
        elif action == "create_draft":
            return self._create_draft(service, params or {})
        else:
            logger.error(f"Invalid action: {action}")
            return f"Invalid action: {action}"

    def _get_credentials(self):
        creds = None
        token_path = 'token.json'
        scopes = ['https://www.googleapis.com/auth/gmail.modify']

        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, scopes)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing credentials...")
                creds.refresh(Request())
            else:
                logger.info("Initiating OAuth flow...")
                flow = InstalledAppFlow.from_client_config({
                    "installed": {
                        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token"
                    }
                }, scopes)
                creds = flow.run_local_server(port=0)
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())

        return creds

    def _read_unread_emails(self, service, params: dict) -> str:
        max_results = params.get('max_results', 10)
        logger.info(f"Fetching up to {max_results} unread emails...")
        results = service.users().messages().list(userId='me', q='is:unread', maxResults=max_results).execute()
        messages = results.get('messages', [])
        logger.info(f"Found {len(messages)} unread emails.")
        relevant_emails = []

        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            headers = {h['name']: h['value'] for h in msg['payload']['headers']}
            sender = headers.get('From', '')
            subject = headers.get('Subject', '')
            logger.info(f"Processing email ID {message['id']} from {sender}: {subject}")
            if not any(keyword in subject.lower() for keyword in ['newsletter', 'otp', 'verification']):
                relevant_emails.append({'email_id': message['id'], 'sender': sender, 'subject': subject})

        logger.info(f"Relevant emails: {relevant_emails}")
        return json.dumps(relevant_emails)

    def _create_draft(self, service, params: dict) -> str:
        email_id = params.get('email_id')
        sender = params.get('sender')
        reply_content = params.get('reply_content', "I'm currently out of the office until July 1, 2025. I'll respond upon my return.")
        logger.info(f"Creating draft for email ID {email_id} to {sender}")
        message = MIMEText(reply_content)
        message['to'] = sender
        message['subject'] = 'Out-of-Office Reply'
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        draft = service.users().drafts().create(userId='me', body={'message': {'raw': raw_message}}).execute()
        logger.info(f"Draft created for email ID {email_id}")
        return f"Draft created for email ID {email_id}"
