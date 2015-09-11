import json
import urllib2
import difflib
try:
    import httplib2
except:
    print "The python 'httplib2' module is a requirement. See https://github.com/jcgregorio/httplib2"
    exit()
#-------------------
# A wrapper class that does the stuff we need with MAL: find aliases and deduce season numbers
# Some of this code is adapted from malconstrict, a MAL api python wrapper
class MalWrapper:
    def __init__(self):
        self.malapiurl = 'https://api.atarashiiapp.com/1'
        self.the_mal_entry = -1
        self.cur_query = ""

    def __raw_search_anime(self, query):
        h = httplib2.Http()
        resp, content = h.request(self.malapiurl + '/anime/search?q=' + urllib2.quote(query))
        print self.malapiurl + '/anime/search?q=' + urllib2.quote(query)
        if int(resp['status']) != 200:
            return None
        return content

    def __raw_get_anime_details(self, anime_id):
        h = httplib2.Http()
        resp, content = h.request(self.malapiurl + '/anime/' + str(anime_id) + '?mine=0')

        if int(resp['status']) == 404:
            return None
        return content

    # tries to find the "best match" series entry on MAL for given query
    def get_mal_entry(self, query):
        if self.the_mal_entry != -1 and self.cur_query == query:
            return self.the_mal_entry;
        self.cur_query = query
        min_acceptable_score = 0.7
        entries = json.loads(self.__raw_search_anime(query))
        # put some back into finding the best result!
        details = None
        while len(entries) > 0:
            # first we try and pick out the best title match
            best_score = 0
            best_match_index = 0
            for i in range(len(entries)):
                if self.__match_score(entries[i]['title'], query) > best_score:
                    best_score = self.__match_score(entries[i]['title'], query)
                    best_match_index = i
            best_match = entries.pop(best_match_index)
            if (best_match['type'] != "TV"):
                continue # we ignore non TV-series for now
            details = json.loads(self.__raw_get_anime_details(best_match['id']))
            print("Evaluating "+ details['title'])
            # then we check if there is at least one alias meeting the minimum score
            if (self.__match_score(details['title'], query) > min_acceptable_score):
                break;
            if 'english' in details['other_titles']:
                found = False
                for title in details['other_titles']['english']:
                    print("Evaluating "+ title)
                    if (self.__match_score(title, query) > min_acceptable_score):
                        found = True
                        break
                if found:
                    break
            if 'synonyms' in details['other_titles']:
                found = False
                for title in details['other_titles']['synonyms']:
                    print("Evaluating "+ title)
                    if (self.__match_score(title, query) > min_acceptable_score):
                        found = True
                        break
                if found:
                    break
            details = None
        return details

    # finds aliases
    def get_other_titles(self, query):
        details = self.get_mal_entry(query)
        result = None
        if details:
            result = [details['title']]
            if 'english' in details['other_titles']:
                for title in details['other_titles']['english']:
                    result.append(title)
                    if title[-6:].lower() == "season":
                        if title[-10:-9] == "1" and title[-9:-7].lower() == "st":
                            result.append(title[0:-10])
                        if title[-10:-9] == "2" and title[-9:-7].lower() == "nd":
                            result.append(title[0:-10])
                        if title[-10:-9].isdigit() and title[-9:-7].lower() == "th":
                            result.append(title[0:-10])
            if 'synonyms' in details['other_titles']:
                for title in details['other_titles']['synonyms']:
                    result.append(title)
                    if title[-6:].lower() == "season":
                        if title[-10:-9] == "1" and title[-9:-7].lower() == "st":
                            result.append(title[0:-10])
                        if title[-10:-9] == "2" and title[-9:-7].lower() == "nd":
                            result.append(title[0:-10])
                        if title[-10:-9].isdigit() and title[-9:-7].lower() == "th":
                            result.append(title[0:-10])
        return result

    # well, deduces season number
    def deduce_season(self, query, default):
        details = self.get_mal_entry(query)
        if details:
            print("Deducing season number with MAL..")
            # firstly, a lot of shows list sequel shows as "<showname> Nth Season"
            # in the synonym list, we look for that, and assume that "Nth Season"
            # isn't actually part of the real title
            # TODO: think harder about this assumption, can we avoid it?
            if 'synonyms' in details['other_titles']:
                for title in details['other_titles']['synonyms']:
                    if title[-6:].lower() == "season":
                        if title[-10:-9] == "1" and title[-9:-7].lower() == "st":
                            print("Deduced season with synonym " + title)
                            return 1
                        elif title[-10:-9] == "2" and title[-9:-7].lower() == "nd":
                            print("Deduced season with synonym " + title)
                            return 2
                        elif title[-10:-9].isdigit() and title[-9:-7].lower() == "th":
                            print("Deduced season with synonym " + title)
                            return int(title[-10:-9])
            # well that didn't work, guess we need to do it the hard way.
            # basically, we see if a prequel is specified, and if it is, we look
            # and see if the prequel has a prequel, and we deduce the season by
            # counting the length of the prequel chain, assuming the end of the chain is
            # season 1
            season_count = 0
            curentry = details
            while True:
                if curentry['type'] == "TV":
                    print("Prequel count at " + curentry['title'] + " : " + str(season_count))
                    season_count += 1
                if len(curentry['prequels']) < 1:
                    break
                curentry = json.loads(self.__raw_get_anime_details(curentry['prequels'][0]['anime_id']))
            if season_count > 1:
                return season_count
        return default

    def __match_score(self, str1, str2):
        return difflib.SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
