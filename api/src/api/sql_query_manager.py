import os
from aiomysql import Connection
from dataclasses import dataclass

class SQLParseError(Exception):
    pass

@dataclass
class SQLQuery:
    query: str
    args: tuple = ()

class SQLQueryManager:
    def __init__(self):
        self.queries = {}

    def load_dir(self, path):
        if not os.path.isdir(path):
            raise ValueError(f"Path '{path}' is not a directory")
        
        for file in os.listdir(path):
            if file.endswith(".sql"):
                with open(os.path.join(path, file)) as f:
                    self.queries[file[:-4]] = f.read()

    async def execute(self, name, cursor, *args, **kwargs):
        try:
            await cursor.execute(self.queries[name], *args, **kwargs)
        except Exception as e:
            raise SQLParseError(f"Error executing query '{name}': {e}")

    def get(self, name):
        return self.queries[name]
    
    def __getitem__(self, name):
        return self.get(name)
    
    def __contains__(self, name):
        return name in self.queries
    
    def __iter__(self):
        return iter(self.queries)
    
    def __len__(self):
        return len(self.queries)
    
    def __repr__(self):
        return f"<SQLQueryManager {len(self)} queries>"
    
    def __str__(self):
        return repr(self)