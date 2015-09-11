import json
import urllib2
import difflib
import re
import xml.etree.ElementTree as ET
try:
    import httplib2
except:
    print "The python 'httplib2' module is a requirement. See https://github.com/jcgregorio/httplib2"
    exit()

class ANNWrapper:
    def __init__(self):
        self.annapiurl = 'http://cdn.animenewsnetwork.com/encyclopedia/'
        self.the_ann_entry = -1
        self.cur_query = ""

    def __raw_search_anime(self, query):
        h = httplib2.Http()
        resp, content = h.request(self.annapiurl + 'reports.xml?id=155&type=anime&search=' + urllib2.quote(query))
        print self.annapiurl + 'reports.xml?id=155&type=anime&search=' + urllib2.quote(query)
        if int(resp['status']) != 200:
            return None
        return content

    def __raw_get_anime_details(self, anime_id):
        h = httplib2.Http()
        resp, content = h.request(self.annapiurl + 'api.xml?anime=' + str(anime_id))
        print self.annapiurl + 'api.xml?anime=' + str(anime_id)
        if int(resp['status']) == 404:
            return None
        return content

    # tries to find the "best match" series entry on MAL for given query
    def get_ann_entry(self, query):
        if self.the_ann_entry != -1 and self.cur_query == query:
            return self.the_ann_entry;
        self.cur_query = query
        min_acceptable_score = 0.7
        entries = ET.fromstring(self.__raw_search_anime(query)).findall('item')
        # put some back into finding the best result!
        details = None
        while len(entries) > 0:
            # first we try and pick out the best title match
            best_score = 0
            best_match_index = 0
            for i in range(len(entries)):
                if self.__match_score(entries[i].find('name').text, query) > best_score:
                    best_score = self.__match_score(entries[i].find('name').text, query)
                    best_match_index = i
            best_match = entries.pop(best_match_index)
            if (best_match.find('type').text != "TV"):
                continue # we ignore non TV-series for now
            details = ET.fromstring(self.__raw_get_anime_details(best_match.find('id').text)).find('anime')
            title = ""
            alts = []
            for info in details.findall("info"):
                if info.get('type') == "Main title":
                    title = info.text
                elif info.get('type') == "Alternative title":
                    alts.append(info.text)
            print("Evaluating "+ title)
            # then we check if there is at least one alias meeting the minimum score
            if (self.__match_score(title, query) > min_acceptable_score):
                break;
            for alt in alts:
                if (self.__match_score(alt, query) > min_acceptable_score):
                    return details
            details = None
        if details is None:
            newquery = query.replace("-"," ");
            newquery = newquery.replace("_"," ");
            newquery = newquery.replace("~"," ");
            newquery2 = query.replace("-","");
            newquery2 = newquery2.replace("_","");
            newquery2 = newquery2.replace("~","");
            if (newquery[0:4].lower() == "the "):
                newquery = newquery[4:]
            if (newquery2[0:4].lower() == "the "):
                newquery2 = newquery2[4:]
            if newquery == query:
                newquery = re.sub(r'ou', r'o', newquery)
                newquery2 = re.sub(r'ou', r'o', newquery2)
            if newquery != query:
                attempt = self.get_ann_entry(newquery)
                if attempt is None:
                    attempt = self.get_ann_entry(newquery2)
                else:
                    return attempt
        return details

    def get_production_studio(self, query):
        entry = self.get_ann_entry(query)
        if entry is not None:
            for credit in entry.findall("credit"):
                if credit.find('task').text == "Animation Production":
                    return credit.find('company').text
        return None

    def __match_score(self, str1, str2):
        return difflib.SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
