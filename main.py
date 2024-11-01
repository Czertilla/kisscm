from datetime import datetime
from pygit2 import Commit, Diff, Oid, Repository
from pygit2.enums import SortMode
import requests
import base64
from tqdm import tqdm
from json import load
from python_mermaid.diagram import (
    MermaidDiagram,
    Node,
    Link
)
with open("config.json", "rb") as config_file:
    config: dict[str, str] = load(config_file)
REPO_PATH = config.get("REPO_PATH", ".git")
FILENAME = config.get("FILENAME", "README")
RENDER_PATH = config.get("RENDER_PATH", "https://mermaid.ink/img/")
commits_count = 0
#
repo = Repository(REPO_PATH)


def is_have_target_patch(diff: Diff, filename: str) -> bool:
    for patch in (diff):
        path = patch.delta.new_file.path.split("/")
        if filename in path:
            return True
    else:
        return False


def is_have_target_diff(commit: Commit, filename: str) -> bool:
    if not commit.parents:
        diff = commit.tree.diff_to_tree(swap=True)
        if is_have_target_patch(diff, filename):
            return True
    for parent in commit.parents:
        diff = commit.tree.diff_to_tree(parent.tree)
        if is_have_target_patch(diff, filename):
            return True
    else:
        return False


def iterate_repository(repo: Repository) -> list[Commit]:
    commits: set[Commit] = set()
    moshpit: set[Commit] = set()
    for branch_name in tqdm(list(repo.branches), position=0, ncols=80, desc="scanning branches"):
        branch = repo.branches.get(branch_name)
        oid = branch.target
        if not isinstance(oid, Oid):
            continue
        global commits_count
        for commit in tqdm(repo.walk(oid, SortMode.TIME), position=1, ncols=80, leave=False, desc=branch_name):
            if commit in commits | moshpit:
                continue
            commits_count += 1
            if is_have_target_diff(commit, FILENAME):
                commits.add(commit)
            else:
                moshpit.add(commit)
    return list(commits)


def find_parents(commit: Commit, commits: list[Commit]) -> tuple[list[Commit], list[bool]]:
    i = 0
    result: list[Commit] = [] + commit.parents
    parent_print = []
    while not (set(result) <= set(commits)):
        parent_print += [False for _ in range(
            max(0, len(result) - len(parent_print)))]
        parent = result[i]
        if parent not in commits:
            parent_print[i] = False
            result.pop(i)
            if len(parent.parent_ids) == 2:
                i = i
            result += parent.parents
        else:
            parent_print[i] = True
            i = (i + 1) % len(result)
    return list(set(result)), parent_print


commits: list[Commit] = iterate_repository(repo)
print(f"{commits_count} have been scanned")
nodes: dict[str, Node] = {
    commit.id:
    Node(
        str(commit.id),
        content=f"{str(commit.id)[:6]}..\n{commit.author.name}\n{datetime.fromtimestamp(commit.commit_time)}\n"
    ) for commit in tqdm(commits, ncols=80, desc="making nodes")
}
links = []
for commit in tqdm(commits, ncols=80, position=0, desc="making links"):
    parents, parent_print = find_parents(commit, commits)
    links += [
        Link(nodes.get(commit.id), nodes.get(parent.id),
             shape=("normal" if parent_print[i] else "dotted"))
        for i, parent in tqdm(enumerate(parents), position=1, leave=False, ncols=80, desc=f"sha:{str(commit.id)}")
    ]


def render(graph):
    graphbytes = graph.encode("utf8")
    base64_bytes = base64.urlsafe_b64encode(graphbytes)
    base64_string = base64_bytes.decode("ascii")
    try:
        img_data = requests.get(RENDER_PATH + base64_string).content
    except:
        print("no connection, graph will save in file backup.graph")
        with open("backup.graph", "w") as file:
            file.write(graph)
        return
    with open('result.jpg', 'wb') as handler:
        handler.write(img_data)
        print("reslut have been saved in file result.jpg")


render(str(MermaidDiagram(title=f"{FILENAME} in {repo.path}", nodes=list(
    nodes.values()), links=links, type="flowchart")))
