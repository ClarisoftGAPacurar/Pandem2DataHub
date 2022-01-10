import os
import datetime
import json
import numpy
import io
import getpass

def check_pandem_home():
  if os.environ.get("PANDEM_HOME") is None:
    raise RuntimeError("The variable PANDEM_HOME needs to be set to a local folder in order to run pandem source")

def pandem_path(*path):
  if os.environ.get("PANDEM_HOME") is None:
    raise RuntimeError("The variable PANDEM_HOME needs to be set to a local folder in order to run pandem source")
  else:
    return os.path.join(os.environ.get("PANDEM_HOME"), *path)


def absolute_to_relative(path, inner_path):
    rel = os.environ.get("PANDEM_HOME")
    if path.startswith(rel):
      path = path[len(rel):len(path)]
    if path.startswith("/") or path.startswith("\\"):
      path = path[1:len(path)]
    rel = inner_path
    if path.startswith(rel):
      path = path[len(rel):len(path)]
    return path

def pretty(o):
  class JsonEncoder(json.JSONEncoder):
    def default(self, z):
      if isinstance(z, datetime.datetime) or isinstance(z, numpy.int64):
        return (str(z))
      else:
        return super().default(z)
  return json.dumps(o,cls=JsonEncoder, indent = 4)

def get_or_set_secret(name):
  secret_dir = pandem_path("secrets")
  if not os.path.exists(secret_dir):
    os.makedirs(name = secret_dir, mode = 0o700)

  secret_path = os.path.join(secret_dir, name)
  if not os.path.exists(secret_path):
    p = getpass.getpass(prompt = f"Password {name} not found, please type it or put a file with its content (UTF-8) in {secret_path}")
    with open(secret_path, 'w', encoding='utf-8') as f:
      f.write(p)
    os.chmod(secret_path, 0o400)
  with io.open(secret_path, mode = "r", encoding = "utf-8") as f:
    return f.read()
       
