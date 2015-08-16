import web
import feedparser
import json
import subprocess
from functions import *
from tvdbmal import MalWrapper
try:
    import tvdb_api
except:
    print "The tvdb python module 1.6.2 needs to be installed. See https://github.com/dbr/tvdb_api"
    exit()


urls = (
    '/', 'index',
    '/addfave', 'addfave',
    '/removefave', 'removefave',
    '/addfavestream', 'addfavestream',
    '/removefavestream', 'removefavestream',
    '/search', 'search',
    '/stream', 'stream',
    '/list', 'list',
    '/test', 'test',
    '/local', 'local',
    '/play', 'play',
    '/nameservice/(.+)', 'nameservice',
)

partial_render = web.template.render('templates/partials')
render = web.template.render('templates/', globals={'urllib': urllib, 'partial_render': partial_render}, base="layout")

class index:
    def GET(self):
        my_shows = get_my_shows()
        tiles = arrange_into_tiles(feedparser.parse('http://www.nyaa.eu/?page=rss&user=64513'), my_shows)
        tiles = arrange_into_tiles(feedparser.parse('http://www.nyaa.eu/?page=rss&user=64513&offset=2'), my_shows, tiles)
        tiles = arrange_into_tiles(feedparser.parse('http://www.nyaa.eu/?page=rss&user=64513&offset=3'), my_shows, tiles)
        tiles = arrange_into_tiles(feedparser.parse('http://www.nyaa.eu/?page=rss&user=64513&offset=4'), my_shows, tiles)
        tiles = arrange_into_tiles(feedparser.parse('http://www.nyaa.eu/?page=rss&user=64513&offset=5'), my_shows, tiles)
        return render.index(tiles, my_shows)

class addfave:
    def GET(self):
        param = web.input(title=None)
        if not param.title == None:
            add_to_my_shows(param.title)
        raise web.seeother('/')

class removefave:
    def GET(self):
        param = web.input(title=None)
        if not param.title == None:
            remove_from_my_shows(param.title)
        raise web.seeother('/')

class addfavestream:
    def GET(self):
        param = web.input(title=None)
        if not param.title == None:
            add_to_my_streams(param.title)
        raise web.seeother('/stream')

class removefavestream:
    def GET(self):
        param = web.input(title=None)
        if not param.title == None:
            remove_from_my_streams(param.title)
        raise web.seeother('/stream')

class search:
    def GET(self):
        param = web.input(title=None)
        my_shows = get_my_shows()
        tiles = arrange_into_tiles(feedparser.parse('http://www.nyaa.eu/?page=rss&user=64513&term=' + urllib.quote_plus(param.title)), my_shows)
        tiles = arrange_into_tiles(feedparser.parse('http://www.nyaa.eu/?page=rss&user=64513&offset=2&term=' + urllib.quote_plus(param.title)), my_shows, tiles)
        return render.search(tiles, my_shows)

class stream:
    def GET(self):
        my_streams = get_my_streams()
        tiles = get_daisuki_tiles(my_streams)
        return render.stream(tiles, my_streams)

class list:
    def GET(self):
        param = web.input(ad_id=None,title=None)
        my_streams = get_my_streams()
        eps = get_daisuki_episodes(param.ad_id)
        return render.list(eps, my_streams, param.title)

class local:
    def GET(self):
        files = get_files_from('/home/lim/Videos')
        return render.local(files)

class play:
    def GET(self):
        param = web.input(path=None)
        print "/usr/bin/smplayer '"+param.path+"'"
        subprocess.Popen(["/usr/bin/smplayer", param.path])
        return "<script> window.close(); </script>"

class nameservice:
    def GET(self, endpoint):
        param = web.input()
        t = tvdb_api.Tvdb()
        if endpoint == "series" and hasattr(param, 'title'):
            malwrapper = MalWrapper()
            alts = malwrapper.get_other_titles(param.title)
            if alts == None:
                return json.dumps({'status': 'notfound'})
            else:
                for title in alts:
                    try:
                        print "trying " + title
                        return json.dumps({'status': 'ok', 'data': t[title].data, 'season': malwrapper.deduce_season(param.title, 1)})
                    except (tvdb_api.tvdb_shownotfound, tvdb_api.tvdb_seasonnotfound, tvdb_api.tvdb_episodenotfound) as err: 
                        continue
                return json.dumps({'status': 'notfound'})
        elif endpoint == "episode" and hasattr(param, 'seriesname') and hasattr(param, 'seasonnum') and hasattr(param, 'epnum'):
            try:
                curseason = int(param.seasonnum)
                curep = int(param.epnum)
                seasonepcount = len(t[param.seriesname][curseason].keys())
                while curep > seasonepcount:
                    curseason += 1
                    curep -= seasonepcount
                    seasonepcount = len(t[param.seriesname][curseason].keys())
                return json.dumps({'status': 'ok', 'data': t[param.seriesname][curseason][curep] })
            except (tvdb_api.tvdb_shownotfound, tvdb_api.tvdb_seasonnotfound, tvdb_api.tvdb_episodenotfound) as err: 
                return json.dumps({'status': 'notfound'})
        else:
            return json.dumps({'status': 'error', 'errormsg': 'invalid endpoint' })
            

class test:
    def GET(self):
        #page = requests.get('http://www.daisuki.net/anime/detail/WORKING3').text
        #m = re.search('class="episodeNumber"><a href="(.*)">1</a>', page)
        #return m.group(1)
        page = requests.get('http://www.daisuki.net/anime/detail/WORKING3').text
        m = re.search('class="episodeNumber">5</p>\n\s+<div class="play"><a href="(.*)"></a>', page)
        return m.group(1)
        #return requests.get('http://www.daisuki.net/fastAPI/anime/search').text

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.run()