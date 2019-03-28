#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-
"""
Description:
    #TODO

::

    usage:
        wiki_load.py    --action=STR --url=STR --user=STR --password=STR --wikipage=DIR [--bots=INT] [-v]

    option:
        -h --help    Show help.
        -v   print info.
"""


import aiowiki
import asyncio
import aiohttp
import os
import sys
import time
import docopt

async def main(loop):
    args = docopt.docopt(__doc__)
    wiki_url = args["--url"]
    user = args["--user"]
    password = args["--password"]
    wikipage_folder = args["--wikipage"]
    if args["--bots"]:
        nb_bots = int(args["--bots"])
    else:
        nb_bots = 1
    action = args["--action"]
    verbose = args["-v"]

    wiki = aiowiki.Wiki(wiki_url)
    await wiki.login(user, password)
    if action in ["load", "check"]:
        list_of_pages = list_pages(wikipage_folder)
        print("nb pages: %s" %len(list_of_pages))
        chuncked_list_of_pages = chunkify(list_of_pages, nb_bots)
        nb_sleeping_worker = len([chunck for chunck in chuncked_list_of_pages if not chunck])
        if nb_sleeping_worker:
            nb_bots = nb_bots - nb_sleeping_worker
            print("to many worker used, only %s are required" %nb_bots)
        try:
            bots_data = await create_bot(wiki, nb_bots)
            for index, item in enumerate(bots_data.items()):
                bot_name, data = item
                bot_password = data["password"]
                worker = aiowiki.Wiki(wiki_url)
                await worker.login(bot_name, bot_password)
                chunck_part = chuncked_list_of_pages[index]
                data["chunck_part"] = chunck_part
                data["worker"] = worker
                data["verbose"] = verbose
            tasks = []
            for bot_data in bots_data.values():
                if action == "load":
                    tasks.append(asyncio.create_task(load_page(bot_data)))
                elif action == "check":
                    tasks.append(asyncio.create_task(check_page(bot_data)))
            await asyncio.gather(*tasks)
        finally:
            for data in bots_data.values():
                worker = data["worker"]
                await worker.close()
            await wiki.close()

async def create_bot(wiki, nb_bots):
    print("Check bots:")
    bots_data = dict()
    for i in range(nb_bots):
        bot_name = "bot_{0}".format(i)
        bot_password = "bot_{0}_password".format(i)
        bot_email = "{0}.{0}@bot.com".format(bot_name)
        bots_data[bot_name] = {"password": bot_password, "bot_name":bot_name}
        try:
            await wiki.create_account(bot_name, bot_password, bot_email)
            print("{0} created".format(bot_name))
        except aiowiki.exceptions.CreateAccountError:
            print("{0} already existing".format(bot_name))
        try:
            await wiki.userrights(bot_name, "add", "bureaucrat")
        except aiowiki.exceptions.UserRightsNotChangedError:
            pass

    return bots_data

async def load_page(bot_data):
    bot_name, worker, chunck_part, verbose = bot_data["bot_name"], bot_data["worker"], bot_data["chunck_part"], bot_data["verbose"]
    for file_index, filepath in enumerate(chunck_part):
        file_index += 1
        remaining_files = len(chunck_part) - file_index
        title = os.path.basename(filepath).replace("__47__", "/")
        retries = 0
        success = False
        last_exc = None
        while not success and retries < 5:
            try:
                p = worker.get_page(title)
                with open(filepath, 'r') as content_file:
                    await p.edit(content_file.read())
                success = True
            except:
                e = sys.exc_info()[0]
                retries += 1
                #print('[Info] Failed to load page "%s", retrying in %s seconds...' % (title, retries))
                last_exc = e
                time.sleep(retries)

        if success:
            if verbose:
                print('%s uploaded page %s , %s done (%s remaining)' % (bot_name, title, file_index, remaining_files))
        else:
            if last_exc:
                print('[WARNING] Failed to load page "%s" (%s). Error: %s' % (title, filepath, last_exc), file=sys.stderr)
            else:
                # Not supposed to happen, but who knows...
                print('[WARNING] Failed to load page "%s" (%s). Unable to catch error source from exceptions' % (title, filepath))


async def check_page(bot_data):
    bot_name, worker, chunck_part, verbose = bot_data["bot_name"], bot_data["worker"], bot_data["chunck_part"], bot_data["verbose"]
    for file_index, filepath in enumerate(chunck_part):
        file_index += 1
        remaining_files = len(chunck_part) - file_index
        title = os.path.basename(filepath).replace("__47__", "/")
        title = title.replace("+", "%2B")
        if verbose:
            print("%s checking page %s, %s done, %s remaining pages to check" %(bot_name, title, file_index, remaining_files))
        retries = 0
        success = False
        last_exc = None
        max_retries = 5
        while not success and retries < max_retries:
            try:
                p = worker.get_page(title)
                try:
                    host_data = await p.markdown()
                    host_data_array = host_data.splitlines()
                    with open(filepath, 'r') as content_file:
                        local_data_array = content_file.read().splitlines()
                    success = True
                    if local_data_array != host_data_array:
                        print("difference found in %s" % title)

                except aiowiki.exceptions.PageNotFound:
                    print("Page %s not found" %title)
                    retries = max_retries
                    last_exc = aiowiki.exceptions.PageNotFound
            except (aiowiki.exceptions.EditError, aiohttp.client_exceptions.ServerDisconnectedError) as e:
                retries += 1
                print('Failed to load "%s", retrying in %s seconds...' % (title, retries))
                last_exc = e
                time.sleep(retries)

        if not success:
            if last_exc:
                print('[WARNING] Failed to load page "%s" (%s). Error: %s' % (title, filepath, last_exc), file=sys.stderr)
            else:
                # Not supposed to happen, but who knows...
                print('[WARNING] Failed to load page "%s" (%s). Unable to catch error source from exceptions' % (title, filepath))


def list_pages(dirName):
    # create a list of file and sub directories
    # names in the given directory
    listOfFile = os.listdir(dirName)
    if "files" in listOfFile: listOfFile.remove("files")
    #if "navigation" in listOfFile: listOfFile.remove("navigation")
    allFiles = list()
    # Iterate over all the entries
    for entry in listOfFile:
        # Create full path
        fullPath = os.path.join(dirName, entry)
        # If entry is a directory then get the list of files in this directory
        if os.path.isdir(fullPath):
            allFiles = allFiles + list_pages(fullPath)
        else:
            allFiles.append(fullPath)

    return allFiles

def chunkify(lst, n):
    return [lst[i::n] for i in range(n)]


if __name__ == '__main__':
    #asyncio.get_event_loop().run_until_complete(main())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))