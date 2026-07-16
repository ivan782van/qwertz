from git import Repo
import os


def update_repository(url, local_path):

    if not os.path.exists(local_path):

        Repo.clone_from(url, local_path)

    else:

        repo = Repo(local_path)

        repo.remotes.origin.pull()

    return Repo(local_path)
