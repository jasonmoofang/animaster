import re
import urllib
import requests
import json
import os

def process_filename (name):
    strip = '[\\s(\\[\\-_][0-9]{4}x[0-9]{3}[\\s)\\]\\-_]?,[\\s(\\[\\-_][0-9]{4}x[0-9]{4}[\\s)\\]\\-_]?,[\\s(\\[\\-_][0-9]{3}x[0-9]{3}[\\s)\\]\\-_]?,^\\[[^\]]+\\],v[0-9]+'.split(',')
    title = name
    for ex in strip:
      title = re.sub(re.compile(ex), r'', title)
    title = re.sub(r'_', r' ', title)
    print title
    searchObj = re.match(r'(.*)\s?\-\s?([0-9]{2,3})[\s\-_](\[[0-9]{3,4}p\]).*', title)
    if searchObj:
      return {
        'title': searchObj.group(1).strip(),
        'episode': searchObj.group(2).strip(),
        'res': searchObj.group(3).strip()
      }
    else:
      searchObj = re.match(r'(.*)\s?\-\s?([0-9]{2,3})[\s\-_].*', title)
      if searchObj:
        return {
          'title': searchObj.group(1).strip(),
          'episode': searchObj.group(2).strip(),
          'res': "res unknown"
        }
      return False

def get_my_shows ():
    with open('myshows.cfg', 'r') as content_file:
        content = content_file.read().split(',')
    if len(content) == 1 and content[0].strip() == "":
        return []
    for i,c in enumerate(content):
        content[i] = urllib.unquote_plus(c)
    return content
  
def add_to_my_shows (title):
    with open('myshows.cfg', 'r') as content_file:
        content = content_file.read().split(',')
    if len(content) == 1 and content[0].strip() == "":
        content = []
    content.append(urllib.quote_plus(title))
    with open('myshows.cfg', 'w') as content_file:
        content_file.write(','.join(content))

def remove_from_my_shows (title):
    with open('myshows.cfg', 'r') as content_file:
        content = content_file.read().split(',')
    if len(content) == 1 and content[0].strip() == "":
        content = []
    for i,c in enumerate(content):
        if title == urllib.unquote_plus(c):
            del content[i]
    with open('myshows.cfg', 'w') as content_file:
        content_file.write(','.join(content))

def get_my_streams ():
    with open('mystreams.cfg', 'r') as content_file:
        content = content_file.read().split(',')
    if len(content) == 1 and content[0].strip() == "":
        return []
    for i,c in enumerate(content):
        content[i] = urllib.unquote_plus(c)
    return content
  
def add_to_my_streams (title):
    with open('mystreams.cfg', 'r') as content_file:
        content = content_file.read().split(',')
    if len(content) == 1 and content[0].strip() == "":
        content = []
    content.append(urllib.quote_plus(title))
    with open('mystreams.cfg', 'w') as content_file:
        content_file.write(','.join(content))

def remove_from_my_streams (title):
    with open('mystreams.cfg', 'r') as content_file:
        content = content_file.read().split(',')
    if len(content) == 1 and content[0].strip() == "":
        content = []
    for i,c in enumerate(content):
        if title == urllib.unquote_plus(c):
            del content[i]
    with open('mystreams.cfg', 'w') as content_file:
        content_file.write(','.join(content))

def arrange_into_tiles (feed, my_shows, tiles = None):
    if tiles == None:
        tiles = { 'my_shows': [], 'other': [] }
    for ent in feed['entries']:
        info = process_filename(ent['title'])
        if info == False:
            print "ignored"
            #tiles['other']['Other Shows'].append({ 'title': ent['title'], 'link': ent['link'], 'date': ent['published'] })
        else:
            info['link'] = ent['link']
            info['date'] = ent['published']
            if info['title'] in my_shows:
                added = False
                for show in tiles['my_shows']:
                    if show['title'] == info['title']:
                        for ep in show['episodes']:
                            if ep['episode'] == info['episode']:
                                ep['files'][info['res']] = info
                                added = True
                        if not added:
                            show['episodes'].append({ 'episode': info['episode'], 'files': { info['res']: info } })
                        added = True
                if not added:
                    tiles['my_shows'].append({ 'title': info['title'], 'episodes': [ { 'episode': info['episode'], 'files': { info['res']: info } } ] })
            else:
                added = False
                for show in tiles['other']:
                    if show['title'] == info['title']:
                        for ep in show['episodes']:
                            if ep['episode'] == info['episode']:
                                ep['files'][info['res']] = info
                                added = True
                        if not added:
                            show['episodes'].append({ 'episode': info['episode'], 'files': { info['res']: info } })
                        added = True
                if not added:
                    tiles['other'].append({ 'title': info['title'], 'episodes': [ { 'episode': info['episode'], 'files': { info['res']:  info } } ] })
    return tiles

def get_daisuki_tiles (my_streams):
    shows = json.loads(requests.get('http://www.daisuki.net/fastAPI/anime/search').text)
    tiles = { 'my_shows': [], 'other': [] }
    for show in shows['response']:
        show['title'] = show['title'].encode('ascii', 'ignore').decode('ascii');
        if show['title'] in my_streams:
            show['episodes'] = get_daisuki_episodes(show['ad_id'])
            tiles['my_shows'].append(show)
        else:
            tiles['other'].append(show)
    return tiles

def get_daisuki_episodes (ad_id):
    page = requests.get('http://www.daisuki.net/anime/detail/'+ad_id).text
    print 'http://www.daisuki.net/anime/detail/'+ad_id
    episodes = []
    for i in range(1000):
        m = re.search('class="episodeNumber"><a href="(.*)">'+str(i+1)+'</a>', page)
        if m:
            episodes.append('http://www.daisuki.net/'+m.group(1))
        else:
            m = re.search('class="episodeNumber">'+str(i+1)+'</p>\n\s+<div class="play"><a href="(.*)"></a>', page)
            if m:
                episodes.append('http://www.daisuki.net/'+m.group(1))
            else:
                break
    return episodes

def get_files_from (folder):
    relevant_path = folder
    included_extenstions = ['mkv','avi','mp4','mpg' ] ;
    file_names = [] #[fn for fn in os.listdir(relevant_path) if any([fn.endswith(ext) for ext in included_extenstions])];
    for root, dirs, files in os.walk(folder, followlinks=True):
      for file in files:
          if any([file.endswith(ext) for ext in included_extenstions]):
              file_names.append(file)
    ret = []
    for f in file_names:
        info = process_filename(f)
        if info:
            info['path'] = folder+'/'+f
            added = False
            for s in ret:
                if s['title'] == info['title']:
                    s['episodes'][int(info['episode'])] = info
                    if s['max_episode'] < info['episode']:
                        s['max_episode'] = info['episode']
                    added = True
                    break
            if not added:
                ret.append({ 'title': info['title'], 'max_episode': info['episode'], 'episodes': { int(info['episode']): info } })
    return ret
