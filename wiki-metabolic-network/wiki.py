#!/usr/bin/env python3.7
"""
Description:
    Tool for wiki management.
    Works without setting in docker image docker.io/dyliss/wiki-metabolic-network-img.
    To create a new wiki use:

        wiki --init=ID [--access=STR]

        set init: as the name of your wiki.

        Will check if a wiki already exist in wiki_folder and in the database.

        set access: 

            'private' to create a wiki preventing access and editing for non-user. Prevent account creation (confidential data).

            'public' to create a wiki allowing access and editing for non-user. Allow account creation.

        After running the command simply the instructions on the terminal.

    To remove a wiki use:

        wiki --id=ID --remove
        
        will remove wiki from wiki_folders and remove table from database which start with prefix ID_.
        
    To reset a wiki use:
        
        wiki --id=ID --clean
        
        will remove all the pages of a wiki only.
    
    To change access rule to a wiki use:
        
    	wiki --id=ID --access=STR

        set access: 

            'private' to create a wiki preventing access and editing for non-user. Prevent account creation (confidential data).

            'public' to create a wiki allowing access and editing for non-user. Allow account creation.
        
    To list all deployed wiki use:

        wiki --all

::

    usage:
    	wiki --init=ID [--access=STR]
    	wiki --id=ID --rebuild
    	wiki --id=ID --clean
    	wiki --id=ID --remove
    	wiki --id=ID --access=STR
    	wiki --all

    options:
    	-h --help    Show help.
    	--init=ID    identifier of the new wiki to initialize.
    	--wiki=ID    identifier of the wiki to manage.
    	--access=STR    set access to wiki as 'public' or 'private'. Default is 'public'.
    	--rebuild    Rebuild SemanticMediaWiki database, Must always be runned after loading/removing pages.
    	--clean    Remove all the pages of a wiki only.
    	--remove    Remove wiki from wiki_folders and remove table from database which start with prefix ID_.
    	--all    list all wiki found in wiki_folders.

"""
import docopt
import os
import subprocess
import shutil
import configparser


def set_var():
    """
    Set global variable by reading config file 'config_file_path'

    """
    global db_host, db_host, db_name, db_user, db_pwd, \
    wiki_host, \
    wiki_folders, wiki_template, forms_path,\
    db_alias

    config_file_path = "/home/wiki.conf"

    config = configparser.ConfigParser()
    config.read(config_file_path)
    #[MYSQL_VAR]
    db_host = config.get('MYSQL_VAR', 'db_host')
    db_name = config.get('MYSQL_VAR', 'db_name')
    db_user = config.get('MYSQL_VAR', 'db_user')
    db_pwd = config.get('MYSQL_VAR', 'db_pwd')
    #[MEDIAWIKI_VAR]
    wiki_host = config.get('MEDIAWIKI_VAR', 'wiki_host')
    #[PATHS]
    wiki_folders = config.get('PATHS', 'wiki_folders')
    wiki_template = config.get('PATHS', 'wiki_template')
    forms_path = config.get('PATHS', 'forms_path')

    db_alias = f'mysql --host={db_host} --user={db_user} --password={db_pwd}'


def main():
    """
    Ref to global doc
    """
    set_var()
    args = docopt.docopt(__doc__)
    access = args["--access"]
    if access == None:
        access = 'public'
    if access not in ['public', 'private']:
        raise ValueError("--access must be in ['private' or 'public'], default value is set as 'public'")
    #check if db wiki_db exist, if no create it
    try:
        cmd = f'{db_alias} -e "show databases" -s | egrep {db_name}'
        out = subprocess.check_output(["/bin/bash", "-i", "-c", cmd])
    except subprocess.CalledProcessError:
        print(f'Init, creating database {db_name}')
        cmd = f'{db_alias} -e "create database "{db_name}"'
        subprocess.call(["/bin/bash", "-i", "-c", cmd])

    if args["--init"]:
        wiki_id = args["--init"]
        wiki_path = os.path.join(wiki_folders, wiki_id)
        print(f'Checking wiki id {wiki_id}...')
        if os.path.exists(wiki_path):
            raise ValueError(f'A wiki with the id {wiki_id} already exist, remove it or change the new wiki id')
        print(f'Checking wiki id {wiki_id}: OK')
        print(f'Checking if the prefix {wiki_id}_ is already used in the database...')
        try:
            cmd = f'{db_alias} -D {db_name} -e "show tables" -s | egrep "^{wiki_id}_"'
            out = subprocess.check_output(["/bin/bash", "-i", "-c", cmd])
            raise ValueError("%s tables found with prefix %s_, a wiki is already using this prefix." %(out.count("\n"), wiki_id))
        except subprocess.CalledProcessError:
            print(f'Checking the if the prefix {wiki_id}_ is already used in the database: OK')
        print("Wiki initialization...")
        print("\tCopying wiki folder")
        cmd = f'cp -r {wiki_template} {wiki_path}'
        subprocess.call(cmd, shell=True)
        localSettings_path = os.path.join(wiki_path, 'LocalSettings.php')
        print("\tUpdating var in LocalSettings.php")
        #wiki_host_for_cmd = wiki_host.replace("/", "\/")
        with open(localSettings_path, 'r') as f:
            localSettings_data = f.read().splitlines()
        new_localSettings_data = []
        for line in localSettings_data:
            if line.startswith("$wgServer ="):
                print(f"\tSetting wiki host url to {wiki_host}")
                new_line = f'$wgServer = "{wiki_host}";'

            elif line.startswith("$wgScriptPath ="):
                print(f"\tSetting wiki id to {wiki_id}")
                new_line = f'$wgScriptPath = "/{wiki_id}";'

            elif line.startswith("$wgDBprefix ="):
                print(f"\tSetting wiki prefix to {wiki_id}_")
                new_line = f'$wgDBprefix = "{wiki_id}_";'

            elif line.startswith("$wgDBserver ="):
                print(f"\tSetting database host {db_host}")
                new_line = f'$wgDBserver = "{db_host}";'

            elif line.startswith("$wgDBname ="):
                print(f"\tSetting database user {db_user}")
                new_line = f'$wgDBname = "{db_name}";'

            elif line.startswith("$wgDBpassword ="):
                print("\tSetting database password")
                new_line = f'$wgDBpassword = "{db_pwd}";'
            else:
                new_line = line
            new_localSettings_data.append(new_line)
        new_localSettings_data = "\n".join(new_localSettings_data)
        with open(localSettings_path, 'w') as f:
            f.write(new_localSettings_data)
        config_access(localSettings_path, access)

        config_url = f'{wiki_host}/{wiki_id}/mw-config/index.php'
        main_url = f'{wiki_host}/{wiki_id}/index.php/Main_Page'
        print("\n")
        print("##############################################################")
        print("MANUAL SETUP IS NOW REQUIRED. Access to this link from your browser:")
        print(f"\t{config_url}")
        print("Follow this instructions to setup mediawiki:")
        print("Language:")
        print("\tContinue->")
        print("Existing wiki:")
        print("\tUpgrade key: 62763ed4b27d11fc")
        print("\tContinue->")
        print("Welcome to MediaWiki!:")
        print("\tContinue->")
        print("Database settings:")
        print("\tContinue->")
        print("Name:")
        print("\tName of wiki: metabolic_network")
        print(r"\tAdministrator account: /!\ Use exactly the same to allow the bot to upload the pages automatically")
        print("\t\tYour username: admin")
        print("\t\tPassword: 123456789")
        print("\tI'm bored already, just install the wiki.")
        print("\tContinue->")
        print("Install:")
        print("\tContinue->")
        print("\tContinue->")
        print("\tDo not save the LocalSettings file")
        print("##############################################################")
        input("When the previous setup is done, press enter to continue...")
        print("\tRunning update.php")
        update_path = os.path.join(wiki_path, 'maintenance/update.php')
        cmd = f'php {update_path}'
        subprocess.call(cmd, shell=True)
        print("Importings manual curation forms")
        importImg_path = os.path.join(wiki_path, 'maintenance/importImages.php')
        cmd = f'php {importImg_path} --extensions=csv {forms_path}'
        subprocess.call(cmd, shell=True)
        print("The wiki is now online and reachable at this link:")
        print(f'\t{main_url}')
        print("You have now to select the folder containing the wiki pages you want to upload on this wiki")
        api_url = f'{wiki_host}/{wiki_id}/api.php'
        print(f'Ex: wiki_load --action=load --url={api_url} --user=STR --password=STR --wikipage=DIR --bots=INT [-v]')

    elif args["--id"]:
        wiki_id = args["--id"]
        wiki_path = os.path.join(wiki_folders, wiki_id)
        if args["--remove"]:
            print(f'Removing wiki {wiki_id}')
            if os.path.exists(wiki_path):
                print("Removing wiki folder")
                shutil.rmtree(wiki_path)
            else:
                print(f'No folder {wiki_path} found')
            try:
                get_all_tables = f'{db_alias} -D {db_name} -e "show tables" -s | egrep "^{wiki_id}_"'
                all_tables = subprocess.check_output(["/bin/bash", "-i", "-c", get_all_tables])
                all_tables = str(all_tables, 'utf-8', 'ignore').splitlines()
                print("%s tables to drop" %len(all_tables))
                cmd = f'{db_alias} -D {db_name} -e "DROP TABLE '+",".join(all_tables)+'"'
                subprocess.call(["/bin/bash", "-i", "-c", cmd])
            except subprocess.CalledProcessError:
                print(f'No tables with prefix {wiki_id}_ found')
        elif args["--clean"]:
            try:
                get_all_tables = f'{db_alias} -D {db_name} -e "show tables" -s | egrep "^{wiki_id}_"'
                all_tables = subprocess.check_output(["/bin/bash", "-i", "-c", get_all_tables])
                all_tables = str(all_tables, 'utf-8', 'ignore').splitlines()
                if wiki_id+"_page" in all_tables:
                    print(f'{wiki_id}_page table to empty')
                    cmd = f'{db_alias} -D {db_name} -e "truncate table {wiki_id}_page"'
                    subprocess.call(["/bin/bash", "-i", "-c", cmd])
            except subprocess.CalledProcessError:
                print("No tables with prefix %s_ found" %wiki_id)
        elif args["--access"]:
            access = args["--access"]
            localSettings_path = os.path.join(wiki_path, 'LocalSettings.php')
            config_access(localSettings_path, access)
        elif args["--rebuild"]:
            rebuildData(wiki_path)
            


    elif args["--all"]:
        print("All deployed wiki:")
        for i in os.listdir(wiki_folders):
            print("\t"+i)

def rebuildData(wiki_path):
    """
    """
    print("\tRunning smw rebuild")
    rebuild_path = os.path.join(wiki_path, 'extensions/SemanticMediaWiki/maintenance/rebuildData.php')
    cmd = f'php {rebuild_path}'
    subprocess.call(cmd, shell=True)

def config_access(localSettings_path, access):
    """
    Edit LocaSetting file 'localSettings_path' to update wiki access.
    if 'acces' == 'public' or None:

        update wiki to public:

            Non-user can read the wiki

            Non-user can create an account

            All user or non-user can edit pages

    elif 'acces' == 'private':

        update wiki to private:

            Non-user can't read the wiki

            Non-user can't create an account

            All user or non-user can't edit pages
            
    Parameters
    ----------
    localSettings_path: str
        path of LocalSettings.php file to edit
    access: str
        access in ['public', 'private']

    """
    if access == 'public':
        bool_access = 'true'
    elif access == 'private':
        bool_access = 'false'
    else:
        raise ValueError("--access must be in ['private' or 'public'], default value is set as 'public'")

    with open(localSettings_path, 'r') as f:
        localSettings_data = f.read().splitlines()
    new_localSettings_data = []

    for line in localSettings_data:
        if line.startswith("$wgGroupPermissions['*']['edit'] = "):
            new_line = f"$wgGroupPermissions['*']['edit'] = {bool_access};"
        elif line.startswith("$wgGroupPermissions['*']['read'] = "):
            new_line = f"$wgGroupPermissions['*']['read'] = {bool_access};"
        elif line.startswith("$wgGroupPermissions['*']['createaccount'] = "):
            new_line = f"$wgGroupPermissions['*']['createaccount'] = {bool_access};"
        else:
            new_line = line
        new_localSettings_data.append(new_line)
    new_localSettings_data = "\n".join(new_localSettings_data)
    with open(localSettings_path, 'w') as f:
        f.write(new_localSettings_data)


if __name__ == "__main__":
    main()
