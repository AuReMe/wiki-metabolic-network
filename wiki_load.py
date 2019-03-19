#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 11 09:53:09 2019

@author: maite
    async def add_right(self, json):
        token = await self.get_token("userrights")
        json["action"] = "userrights"
        json["format"] = "json"
        json["token"] = token
        async with self.session.post(self.url, data=json) as r:
            json = await r.json()
        return True

    async def add_right(
        self, username: str, action: str, group: str):
        if action not in ["add","remove"]:
            print("action must be 'add' or 'remove' only")
            return False
        json = {
            "user": username,
            action: group,
        }
        await self.http.add_right(json)
        return True

"""


import aiowiki, asyncio
import os
import sys
import time
import threading
from concurrent.futures import ProcessPoolExecutor

async def main(loop):
    wiki_url="http://localhost:8080/api.php"
    user="admin"
    password="meziane_1992"
    wikipage_folder="/home/maite/Documents/data/Qikun/wiki/reactions"
    nb_bots=4
    wiki = aiowiki.Wiki(wiki_url)
    await wiki.login(user, password)
    #page = wiki.get_page("My page title")
    #await page.edit("New content goes here")
    action = "load"
    if action == "load":
        list_of_pages = list_pages(wikipage_folder)
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
            #print(bots_data)    
            tasks = []
            for bot_data in bots_data.values():
                # asyncio.create_task for 3.7+
                # ensure_future is 'cos I am on 3.6
                tasks.append(asyncio.create_task(load_page(bot_data)))
            await asyncio.gather(*tasks)


            """
            for bot_data in bots_data.values():
                bot_name, worker, chunck_part = bot_data["bot_name"], bot_data["worker"], bot_data["chunck_part"]
                await load_page(bot_name, worker, chunck_part)
            """
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
        await wiki.userrights(bot_name,"add","bureaucrat")
    return (bots_data)

async def load_page(bot_data):
    bot_name, worker, chunck_part = bot_data["bot_name"], bot_data["worker"], bot_data["chunck_part"]
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
            except (aiowiki.exceptions.EditError) as e:
                retries += 1
                print('Failed, retrying in %s seconds...' % retries)
                last_exc = e
                time.sleep(retries)
    
        if not success:
            if last_exc:
                print('Failed to load page "%s" (%s).' % (title, filepath), file=sys.stderr)
                raise last_exc
            else:
                # Not supposed to happen, but who knows...
                raise Exception('Failed to load page "%s" (%s).' % (title, filepath))
        print('%s upload page %s , %s done (%s remaining)' % (bot_name, title, file_index,remaining_files))


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

def chunkify(lst,n):
    return [lst[i::n] for i in range(n)]


if __name__ == '__main__':
    #asyncio.get_event_loop().run_until_complete(main())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))    