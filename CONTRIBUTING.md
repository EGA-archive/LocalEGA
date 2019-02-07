# Contributing guidelines

We thank you in advance :thumbsup: :tada: for taking the time to
contribute, whether with *code* or with *ideas*, to the Local EGA
project.


## Did you find a bug?

* Ensure that the bug was not already reported by [searching under Issues].

* If you're unable to find an (open) issue addressing the problem, [open a new
  one]. Be sure to prefix the issue title with **[BUG]** and to include:

  - a *clear* description,
  - as much relevant information as possible, and
  - a *code sample* or an (executable) *test case* demonstrating the expected behaviour that is not occurring.

* If possible, use the following [template to report a bug].


## Highlevel overview of how we work

### Github projects

We use the [Local EGA](https://github.com/orgs/EGA-archive/projects/3) github
project in the EGA-Archive to manage our work.

### How we use issues

Issues are the central area for all work.

### Standups

Every day at 10:30 we have standups in Zoom meeting: <id>

### Sprint Reviews and Planning

Approximately every 2 weeks we have sprint reviews and then also a sprint
planning meeting.



## How to work on a new feauture/bug

Create an issue on Github, and talk to the team members on the NBIS local-ega
Slack channel. You can alternatively pick one already created.

Assign yourself to that issue.

Discussions on how to proceed about that issue take place in the comment
section on that issue, beforehand.

The keyword here is *beforehand*. It is usually a good idea to talk about it
first. Somebody might have already some pieces in place, we avoid unnecessary
work duplication and a waste of time and effort.


## How we work with Git

All work take place in feature branches. Give your branch a short descriptive
name and prefix the name with:

   * `feature/` if it is a code feature
   * `hotfix/` if you are fixing an urgent bug

Use comments in your code, choose variable and function names that clearly show
what you intend to implement.

Once the feature is done it is merged back into `master` by making a Pull
Request.


### General stuff about git and commit messages

In general it is better to commit often. Small commits are easier to roll back
and also makes the code easier to review.

Write helpful commit messages that describes the changes and possibly why they
were necessary.

Each commit should contain changes that are functionally connected and/or
related. If you for example want to write _and_ in a commit message this is a
good sign that it should have been two commits.

Learn how to select chunkgs of changed files to do multiple separate commits of
unrelated things. This can be done with either `git add -p` or `git commit -p`.


#### Helpfull commit messages

The commit messages may be seen as meta-comments on the code that are
incredibly helpful for anyone who wants to know how this piece of software is
working, including colleagues (current and future) and external users.

Some tips about writing helpful commit messages:

#. Separate subject (the first line of the message) from body with a blank line.
#. Limit the subject line to 50 characters.
#. Capitalize the subject line.
#. Do not end the subject line with a period.
#. Use the imperative mood in the subject line.
#. Wrap the body at 72 characters.
#. Use the body to explain what and why vs. how.

For an in-depth explanation of the above points, please see [How to Write a Git
Commit Message](http://chris.beams.io/posts/git-commit/).


### How we do code reviews

A code review is initiated by making a Pull Request in the appropriate repo on
github.

Work should not continue on the branch _unless_ it has been marked with the `DO
NOT MERGE` tag. Once the PR is ready and the `DO NOT MERGE` tag is removed the
review process can go on to the next stage.

Before review starts it is a good idea to rebase your branch to `master` to
ensure that we can make a clean merge.

The initiator of the PR should recruit 2 reviewers that get assigned reviewer
duty on the branch. It's not a bad idea to announce this on the #localega slack
channel.

Other people may also look at and review the code.

A reviewers job is to:

  * Read the code and make sure it is understandable
  * Make sure that commit messages and commits are structured so that it is
    possible to understand why certain changes were made.
  * Ensure that the test-suite covers the new behavior

It is _not_ the reviewers job to checkout and run the code - that is what the
test-suite is for.

Once all the reviews are positive the Pull Request can be _merged_ into
`master` and the feature branch deleted.


----

Thanks again,
/NBIS System Developers

[coding guidelines from NBIS]: https://github.com/NBISweden/development-guidelines
[git rebase -i]: https://git-scm.com/book/en/v2/Git-Tools-Rewriting-History
[NBIS reviewing guidelines]: https://github.com/NBISweden/development-guidelines#how-we-do-code-reviews
[searching under Issues]: https://github.com/NBISweden/LocalEGA/issues?utf8=%E2%9C%93&q=is%3Aissue%20label%3Abug%20%5BBUG%5D%20in%3Atitle
[open a new one]: https://github.com/NBISweden/LocalEGA/issues/new?title=%5BBUG%5D
[template to report a bug]: todo
