import click
import json

from oauth2client.service_account import ServiceAccountCredentials
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

try:
    import commands.common as common
except ImportError:
    # Allow running file as standalone
    import common

CONTEXT_SETTINGS = dict(help_option_names=['--help', '-h'])
GOOGLE_SCOPES = ['https://www.googleapis.com/auth/drive']
common_params = common.common_params

@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('file')
@click.option('--gdrive-folder', '-f',
              required=True,
              help='Google Drive folder to upload file into. (URL or folder ID)',
              envvar=common.prefix_envvar('GDRIVE_FOLDER'),
              metavar='<url/id>')
@click.option('--google-creds', '-c',
              type=click.File('rb'),
              required=True,
              envvar=common.prefix_envvar('GOOGLE_CREDS'),
              help='JSON keyfile for a Google service account.',
              metavar='<file>')
@common_params
def upload2gdrive(file, gdrive_folder, google_creds, yes, verbose, debug, noop):
    """Upload local files to a Google Drive folder."""
    folder_id = gdrive_folder
    json_bytes = b''
    while True:
        chunk = google_creds.read(1024)
        if not chunk:
            break
        json_bytes = json_bytes + chunk
    keyfile_dict = json.loads(json_bytes)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(keyfile_dict, GOOGLE_SCOPES)
    if debug: click.echo('>>> Service account email: ' + creds.service_account_email, err=True)
    gauth = GoogleAuth()
    gauth.credentials = creds
    gdrive = GoogleDrive(gauth)
    query = "'{}' in parents".format(folder_id)
    file_list = gdrive.ListFile({'q': query}).GetList()
    filename = file.split('/')[-1]
    match = [f for f in file_list if f['title'] == filename]
    match = match.pop() if match else None
    if match:
        if match['md5Checksum'] == common.get_md5(file):
            click.echo('File exists already. Skipping...', err=True)
        else:
            click.echo('File exists and differs. Overriding...', err=True)
            match.SetContentFile(file)
            match.Upload()

        myfile = match
    else:
        click.echo('Adding file to folder...', err=True)
        new_file = gdrive.CreateFile({'title': filename})
        new_file.SetContentFile(file)
        new_file.Upload()
        new_file.auth.service.parents().insert(fileId=new_file['id'], body={'id': folder_id}).execute()
        new_file.FetchMetadata(fields='permissions')
        # NOTE: We can't change the owner of a non-Drive file with a service account.
        myfile = new_file

    common.echo_config(myfile.metadata, ['webContentLink', 'title'])

if __name__ == '__main__':
    upload2gdrive()
