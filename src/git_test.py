# Put in ./Testing folder when performing testing
from git import Repo
import os
import pathlib
from dotenv import load_dotenv

load_dotenv()

# Clones repository
"""
Repo.clone_from('https://github.com/official-himanshu/JavaPro.git', pathlib.Path(__file__).parent.absolute() / 'JavaPro')
print('Clone repo successful')
"""

# Creates a new repository
# 'git init GitPythonTesting'
repo = Repo('GitPythonTesting')

with repo.config_writer() as git_config:
    git_config.set_value('user', 'email', os.getenv('GIT_EMAIL'))
    git_config.set_value('user', 'name', os.getenv('GIT_NAME'))

# Print values of git_config
with repo.config_writer() as git_config:
    print(git_config.get_value('user', 'email'))
    print(git_config.get_value('user', 'name'))

"""
import git

repo = git.Repo('my_repo')

# Provide a list of the files to stage
repo.index.add(['.gitignore', 'README.md'])
# Provide a commit message
repo.index.commit('Initial commit.')
"""


# Provide a list of files to stage
repo.index.add(['.gitignore', 'README.md'])
for item in repo.index.diff(None):
    print('filename: ', item.a_path)