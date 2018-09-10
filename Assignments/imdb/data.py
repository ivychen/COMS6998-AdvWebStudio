import os
import pickle
import uuid

class Movies():
    class Movie():
        def __init__(self, title, year, desc, cast):
            self._id = str(uuid.uuid4())
            self.title = title
            self.year = year
            self.desc = desc
            self.cast = cast

        @property
        def id(self):
            return self._id

        def __str__(self):
            return(self.title + " " + self.year + " " + self.desc)

    def __init__(self, filename):
        if os.path.getsize(filename) > 0:
            self.dic = self.loadData(filename)
            # for v in self.dic.values():
            #     print(v)
        else:
            self.dic = {}

        self.filename = filename

    def loadData(self, filename):
        with open(filename, 'rb') as file:
            data = pickle.load(file)
        return data

    def saveData(self, filename):
        with open(filename, 'wb') as file:
            pickle.dump(self.dic, file, protocol=pickle.HIGHEST_PROTOCOL)

    def addMovie(self, title, year, desc, cast):
        m = self.Movie(title, year, desc, cast)
        self.dic[m.id] = m
        self.saveData(self.filename)

    def deleteMovie(self, id):
        if id in self.dic:
            del self.dic[id]
            self.saveData(self.filename)
            return id
        else:
            return None
