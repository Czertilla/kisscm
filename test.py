import pytest
from pygit2.repository import Repository
from pygit2 import Oid, Signature, Worktree, init_repository

import os
import shutil
folder = '/path/to/folder'

REPO_PATH = "test/"
FILENAME = "test"
RENDER_PATH = "https://mermaid.ink/img/"


def setup():
    repo = init_repository(REPO_PATH+".git")
    repo.branches


def teardown():
    for filename in os.listdir(REPO_PATH):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

def commit(repository: Repository, user_name="czertilla", user_mail="blaztermapskorsak@gmail.com"):
    index = repository.index
    index.add_all()
    index.write()
    author = Signature(user_name, user_mail)
    commiter = Signature(user_name, user_mail)
    tree = index.write_tree()
    target = repository.head.target
    oid = repository.create_commit(None, author, commiter, "commit", tree, [repository.head.target])
    repository.head.set_target(oid)

def test_is_have_target_patch():
    repo = Repository(REPO_PATH+'.git')
    repo.checkout("main")
    open(REPO_PATH+"test", "a").close()
    commit(repo)

if __name__ == "__main__":
    teardown()
    setup()
    test_is_have_target_patch()