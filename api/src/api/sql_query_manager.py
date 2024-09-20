import os
from glob import glob
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
        
        for file in glob(f"{path}/**/*.sql", recursive=True):
            with open(file, "r") as f:
                name = os.path.splitext(os.path.basename(file))[0]
                self.queries[name] = f.read()

    async def execute(self, name, cursor, *args, **kwargs):
        try:
            await cursor.execute(self.queries[name], *args, **kwargs)
        except KeyError:
            raise SQLParseError(f"Query '{name}' not found")
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